# Copyright (c) 2025, Cruxedge and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from frappe.model.document import Document
import matplotlib
matplotlib.use('Agg')


def four_parameter_logistic(x, min_resp, max_resp, inflection, hill_slope):
    return min_resp + (max_resp - min_resp) / (1 + (x / inflection) ** (-hill_slope))


class DoseResponseCurve(Document):

    def before_save(self):
        # Auto-generate preview plot and attach
        result = self.get_preview_plot()
        self.x50 = result['x50']
        self.equation = result['equation']

        # Save image to file
        content = base64.b64decode(result['plot'].split(',')[1])
        filename = f"dose_response_plot_{self.name}.png"

        # Remove old file if exists
        existing_files = frappe.get_all("File", filters={"attached_to_name": self.name, "attached_to_doctype": self.doctype})
        for f in existing_files:
            frappe.delete_doc("File", f.name)

        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "is_private": 0,
            "content": content,
            "attached_to_doctype": self.doctype,
            "attached_to_name": self.name
        })
        _file.save()

        self.output_view = f"""
            <div>
                <p><strong>X50:</strong> {result['x50']}</p>
                <p><strong>Equation:</strong> {result['equation']}</p>
                <img src="{_file.file_url}" style="max-width: 100%; border: 1px solid #ccc; padding: 8px; border-radius: 6px;">
            </div>
        """

    @frappe.whitelist()
    def get_preview_plot(self):
        conc, resp = self.parse_raw_data(self.raw_data)

        if self.background_correct:
            resp = resp - np.min(resp)
        if self.normalize:
            resp = resp / np.max(resp)

        p0 = [min(resp), max(resp), np.median(conc), 1.0]
        params, _ = curve_fit(four_parameter_logistic, conc, resp, p0=p0, maxfev=10000)
        x50 = round(params[2], 4)

        x_vals = np.logspace(np.log10(min(conc) * 0.5), np.log10(max(conc) * 2), 200)
        y_vals = four_parameter_logistic(x_vals, *params)

        plt.figure(figsize=(6, 4))
        plt.plot(x_vals, y_vals, color='blue', label='4PL Fit')
        plt.scatter(conc, resp, color='black', label='Data')
        plt.axvline(params[2], linestyle='--', color='red', label=f'X50 = {params[2]:.2f}')
        plt.xscale('log')
        plt.xlabel("Concentration (pg/mL)")
        plt.ylabel("Response")
        plt.title("4PL Dose Response Curve")
        plt.legend()
        plt.grid(True)

        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
        data_url = f"data:image/png;base64,{encoded}"

        equation = (
            f"Y = {params[0]:.4f} + ({params[1]:.4f} - {params[0]:.4f}) / "
            f"(1 + (X/{params[2]:.4f})^{params[3]:.4f})"
        )

        return {
            "x50": x50,
            "equation": equation,
            "plot": data_url
        }

    def parse_raw_data(self, raw_data):
        lines = raw_data.strip().splitlines()
        conc = []
        resp = []
        for line in lines:
            if "\t" in line:
                parts = line.split("\t")
            else:
                parts = line.split(",")
            if len(parts) < 2:
                continue
            try:
                conc.append(float(parts[0]))
                resp.append(float(parts[1]))
            except ValueError:
                continue
        return np.array(conc), np.array(resp)