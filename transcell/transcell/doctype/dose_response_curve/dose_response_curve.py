# Copyright (c) 2025, Cruxedge and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from scipy.optimize import curve_fit, root_scalar
import matplotlib
matplotlib.use('Agg')

def four_parameter_logistic(x, min_resp, max_resp, inflection, hill_slope):
    return min_resp + (max_resp - min_resp) / (1 + (x / inflection) ** (-hill_slope))

class DoseResponseCurve(Document):

    def before_save(self):
        result = self.get_preview_plot()
        self.x50 = result['x50']
        self.equation = result['equation']

        # Decode image content from base64
        content = base64.b64decode(result['plot'].split(',')[1])
        filename = f"dose_response_combined_plot_{self.name}.png"

        # Delete any existing files with same name
        existing_files = frappe.get_all("File", filters={
            "attached_to_name": self.name,
            "attached_to_doctype": self.doctype,
            "file_name": filename
        })
        for f in existing_files:
            frappe.delete_doc("File", f.name)

        # Save the file
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "is_private": 0,
            "content": content,
            "attached_to_doctype": self.doctype,
            "attached_to_name": self.name
        })
        _file.save()

        self.set("attachment",_file.file_url)

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

        p0 = [float(min(resp)), float(max(resp)), float(np.median(conc)), 1.0]
        params, _ = curve_fit(four_parameter_logistic, conc, resp, p0=p0, maxfev=10000)
        x50 = round(float(params[2]), 9)

        # Generate x values and predicted y values
        x_vals = np.logspace(np.log10(min(conc) * 0.5), np.log10(max(conc) * 2), 200)
        y_vals = four_parameter_logistic(x_vals, *params)

        # Create subplots
        fig, axs = plt.subplots(1, 2, figsize=(12, 4))

        # Line plot
        axs[0].plot(x_vals, y_vals, color='blue', label='4PL Fit')
        axs[0].scatter(conc, resp, color='black', label='Data')
        axs[0].axvline(params[2], linestyle='--', color='red', label=f'X50 = {params[2]:.9f}')
        axs[0].set_xscale('log')
        axs[0].set_xlabel("Concentration (pg/mL)")
        axs[0].set_ylabel("Response")
        axs[0].set_title("4PL Dose Response Curve")
        axs[0].legend()
        axs[0].grid(True)

        # Bar chart
        axs[1].bar([str(c) for c in conc], resp, color='orange')
        axs[1].set_xlabel("Concentration")
        axs[1].set_ylabel("Response")
        axs[1].set_title("Bar Plot of Raw Data")
        axs[1].tick_params(axis='x', rotation=45)
        axs[1].grid(True)

        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
        data_url = f"data:image/png;base64,{encoded}"

        equation = (
            f"Y = {params[0]:.9f} + ({params[1]:.9f} - {params[0]:.9f}) / "
            f"(1 + (X/{params[2]:.9f})^{params[3]:.9f})"
        )

        self._fitted_params = params

        return {
            "x50": x50,
            "equation": equation,
            "plot": data_url,
            "params": [float(p) for p in params.tolist()]
        }

    def parse_raw_data(self, raw_data):
        lines = raw_data.strip().splitlines()
        conc = []
        resp = []
        for line in lines:
            parts = line.replace(",", "\t").split("\t")
            if len(parts) < 2:
                continue
            try:
                conc.append(float(parts[0]))
                resp.append(float(parts[1]))
            except ValueError:
                continue
        return np.array(conc), np.array(resp)

    @frappe.whitelist()
    def calculate_y_from_x(self, x):
        params = self._fitted_params if hasattr(self, '_fitted_params') else self.get_preview_plot()['params']
        return four_parameter_logistic(float(x), *params)

    @frappe.whitelist()
    def calculate_x_from_y(self, y):
        y = float(y)
        params = self._fitted_params if hasattr(self, '_fitted_params') else self.get_preview_plot()['params']
        min_resp, max_resp = params[0], params[1]

        if not (min_resp <= y <= max_resp):
            frappe.throw(f"Y value {y} out of bounds ({min_resp:.3f} - {max_resp:.3f})")

        def objective(x):
            return four_parameter_logistic(x, *params) - y

        sol = root_scalar(objective, bracket=[1e-6, 1e6], method='brentq')
        if not sol.converged:
            frappe.throw("Failed to calculate X for given Y")

        return round(sol.root, 9)
