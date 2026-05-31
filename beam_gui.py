import customtkinter as ctk
import math
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
import csv
from reportlab.platypus import PageBreak

steel_beams = {}

with open("steel_beams.csv", newline="") as file:

    reader = csv.DictReader(file)

    for row in reader:

        steel_beams[row["shape"]] = {
            "Ix": float(row["Ix"]),
            "moment_capacity": float(row["moment_capacity"])
        }
saved_beams = []

print(f"Loaded {len(steel_beams)} beams")


def calculate(span_ft, load_lb, fos, divisor):
    span_in = span_ft * 12
    allowed_delta = span_in / divisor

    moment_ft_lb = ((load_lb * span_ft) / 8) * fos
    moment_in_lb = moment_ft_lb * 12

    i_required = (
        5 * load_lb * math.pow(span_in, 3)
    ) / (
        384 * (29 * math.pow(10, 6)) * allowed_delta
    )

    i_required_factored = i_required * fos

    return {
        "span_in": span_in,
        "allowed_delta": allowed_delta,
        "moment_ft_lb": moment_ft_lb,
        "moment_in_lb": moment_in_lb,
        "i_required": i_required,
        "i_required_factored": i_required_factored,
    }


def check_beam(beam_name, required_ix):
    beam = steel_beams.get(beam_name)

    if beam is None:
        return "Beam not found"

    if beam["Ix"] >= required_ix:
        return "PASS"

    return "FAIL"

def update_calculations(*args):

    try:
        beam_name = beam_entry.get()

        span_ft = float(span_entry.get())
        load_lb = float(load_entry.get())
        fos = float(fos_entry.get())
        divisor = float(divisor_entry.get())

        results = calculate(
            span_ft,
            load_lb,
            fos,
            divisor
        )

        results_label.configure(
            text=
            f"Span Inches: {results['span_in']:.2f}\n"
            f"Allowed Delta: {results['allowed_delta']:.4f}\n"
            f"Max Bend: {results['moment_ft_lb'] / 1000:.2f}ft-kips\n"
            f"Required Shear: {results['i_required']:.2f}In^4\n"
            f"Max Shear: {results['i_required_factored']:.2f}In^4"
        )

        pass_fail_label.configure(
            text="Beam recommendations generated below"
        )

        recommended = recommend_beams(
            results["i_required_factored"],
            results["moment_ft_lb"] / 1000
        )
        

        recommendation_text = "Recommended Beams:\n\n"

        for beam in recommended:

            recommendation_text += (
            f"{beam[0]} | "
            f"Ix: {beam[1]:.2f} | "
            f"Moment Capacity: {beam[2]:.2f} kip-ft\n"
        
        )
        recommendation_label.configure(
            text=recommendation_text
        )

    except ValueError:
        results_label.configure(
            text="Enter valid numbers for span, load, FOS, and divisor."
        )
        pass_fail_label.configure(text="")
        recommendation_label.configure(text="")

def recommend_beams(required_ix, required_moment):
    matches = []

    for beam_name, properties in steel_beams.items():
        ix_ok = properties["Ix"] >= required_ix
        moment_ok = properties["moment_capacity"] >= required_moment

        if ix_ok and moment_ok:
            matches.append(
                (
                    beam_name,
                    properties["Ix"],
                    properties["moment_capacity"]
                )
            )

    matches.sort(key=lambda x: x[1])

    return matches[:5]

def add_beam_to_report():
    try:
        beam_name = beam_entry.get()
        span_ft = float(span_entry.get())
        load_lb = float(load_entry.get())
        fos = float(fos_entry.get())
        divisor = float(divisor_entry.get())

        results = calculate(span_ft, load_lb, fos, divisor)

        saved_beams.append({
            "beam_name": beam_name,
            "span_ft": span_ft,
            "load_lb": load_lb,
            "fos": fos,
            "divisor": divisor,
            "results": results
        })

        saved_label.configure(text=f"Saved beams: {len(saved_beams)}")

    except ValueError:
        saved_label.configure(text="Cannot save: enter valid numbers.")

def export_pdf():

    doc = SimpleDocTemplate("beam_report.pdf")

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "Beam Report",
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 20))

    for i, beam in enumerate(saved_beams, start=1):

        results = beam["results"]

        table_data = [

            ["Beam Name", beam['beam_name']],
            ["Span (ft)", beam['span_ft']],
            ["Load (lb)", beam['load_lb']],
            ["FOS", beam['fos']],
            ["Deflection Divisor", beam['divisor']],

            ["Span Inches",
             f"{results['span_in']:.2f}"],

            ["Allowed Delta",
             f"{results['allowed_delta']:.4f}"],

            ["Max Bend",
             f"{results['moment_ft_lb']/ 1000:.2f}kip-ft"],

            ["Required Shear",
             f"{results['i_required']:.2f}In^4"],

            ["Max Shear",
             f"{results['i_required_factored']:.2f}In^4"],
        ]

        table = Table(
            table_data,
            colWidths=[200, 200]
        )

        table.setStyle(TableStyle([

            ('GRID', (0, 0), (-1, -1),
             1, colors.black),

            ('BACKGROUND', (0, 0),
             (0, -1), colors.lightgrey),

            ('FONTNAME', (0, 0),
             (-1, -1), 'Helvetica'),

            ('FONTSIZE', (0, 0),
             (-1, -1), 10),

            ('BOTTOMPADDING', (0, 0),
             (-1, -1), 8),

        ]))

        elements.append(
            Paragraph(
                f"Beam {beam['beam_name']}",
                styles["Heading2"]
            )
        )

        elements.append(table)
        recommended = recommend_beams(
            results["i_required_factored"],
            results["moment_ft_lb"] / 1000
        )

        recommended_data = [
            ["Recommended Beam", "Ix", "Moment Capacity"]
        ]

        for rec in recommended:
            recommended_data.append([
            rec[0],
            f"{rec[1]:.2f}",
            f"{rec[2]:.2f} kip-ft"
        ])

        recommended_table = Table(
            recommended_data,
            colWidths=[140, 90, 140]
        )

        recommended_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(Spacer(1, 8))
        elements.append(Paragraph("Recommended Beams", styles["Heading3"]))
        elements.append(recommended_table)
        elements.append(Spacer(1, 8))

        calculation_text = f"""
        <b>Calculation Steps</b><br/>
        Span: {beam['span_ft']} × 12 = {results['span_in']:.2f} in<br/>
        Delta: {results['span_in']:.2f} ÷ {beam['divisor']} = {results['allowed_delta']:.4f} in<br/>
        Max Bend: (({beam['load_lb']} × {beam['span_ft']}) ÷ 8) × {beam['fos']} ÷ 1000 = {results['moment_ft_lb'] / 1000:.2f} ft-lb<br/>
        Required Shear: (5 × {beam['load_lb']} × {results['span_in']:.2f}³) ÷ (384 × 29,000,000 × {results['allowed_delta']:.4f}) = {results['i_required']:.2f}<br/>
        Max Shear: {results['i_required']:.2f} × {beam['fos']} = {results['i_required_factored']:.2f}
        """

        elements.append(
            Paragraph(
                calculation_text,
                styles["BodyText"]
            )
        )

        if i != len(saved_beams):
            elements.append(PageBreak())

    doc.build(elements)

    saved_label.configure(
        text="PDF Exported!"
    )

def clear_inputs():
    beam_entry.delete(0, "end")
    span_entry.delete(0, "end")
    load_entry.delete(0, "end")
    fos_entry.delete(0, "end")
    divisor_entry.delete(0, "end")

    results_label.configure(text="")
    pass_fail_label.configure(text="")
    recommendation_label.configure(text="")

app = ctk.CTk()
app.geometry("900x500")
app.title("Beam Calculator")

input_frame = ctk.CTkFrame(app)
input_frame.grid(row=0, column=0, padx=20, pady=20, sticky="n")

output_frame = ctk.CTkFrame(app)
output_frame.grid(row=0, column=1, padx=20, pady=20, sticky="n")

ctk.CTkLabel(input_frame, text="Inputs", font=("Arial", 22)).grid(row=0, column=0, columnspan=2, pady=10)

ctk.CTkLabel(input_frame, text="Beam Name").grid(row=1, column=0, padx=10, pady=5)
beam_entry = ctk.CTkEntry(input_frame)
beam_entry.grid(row=1, column=1, padx=10, pady=5)

ctk.CTkLabel(input_frame, text="Span (ft)").grid(row=2, column=0, padx=10, pady=5)
span_entry = ctk.CTkEntry(input_frame)
span_entry.grid(row=2, column=1, padx=10, pady=5)

ctk.CTkLabel(input_frame, text="Load (lb)").grid(row=3, column=0, padx=10, pady=5)
load_entry = ctk.CTkEntry(input_frame)
load_entry.grid(row=3, column=1, padx=10, pady=5)

ctk.CTkLabel(input_frame, text="FOS").grid(row=4, column=0, padx=10, pady=5)
fos_entry = ctk.CTkEntry(input_frame)
fos_entry.grid(row=4, column=1, padx=10, pady=5)

ctk.CTkLabel(input_frame, text="Deflection Divisor").grid(row=5, column=0, padx=10, pady=5)
divisor_entry = ctk.CTkEntry(input_frame)
divisor_entry.grid(row=5, column=1, padx=10, pady=5)

ctk.CTkLabel(output_frame, text="Live Calculations", font=("Arial", 22)).grid(row=0, column=0, pady=10)

results_label = ctk.CTkLabel(output_frame, text="", justify="left")
results_label.grid(row=1, column=0, padx=20, pady=20)

pass_fail_label = ctk.CTkLabel(output_frame, text="")
pass_fail_label.grid(row=2, column=0, padx=20, pady=10)
recommendation_label = ctk.CTkLabel(
    output_frame,
    text="",
    justify="left"
)

recommendation_label.grid(
    row=3,
    column=0,
    padx=20,
    pady=20
)

add_button = ctk.CTkButton(
    output_frame,
    text="Add Beam to Report",
    command=add_beam_to_report
)
add_button.grid(row=4, column=0, padx=20, pady=10)

clear_button = ctk.CTkButton(
    output_frame,
    text="New Beam / Clear Inputs",
    command=clear_inputs
)

clear_button.grid(
    row=7,
    column=0,
    padx=20,
    pady=10
)

export_button = ctk.CTkButton(
    output_frame,
    text="Export PDF",
    command=export_pdf
)

export_button.grid(
    row=6,
    column=0,
    padx=20,
    pady=10
)

saved_label = ctk.CTkLabel(output_frame, text="Saved beams: 0")
saved_label.grid(row=5, column=0, padx=20, pady=10)
beam_entry.bind("<KeyRelease>", update_calculations)
span_entry.bind("<KeyRelease>", update_calculations)
load_entry.bind("<KeyRelease>", update_calculations)
fos_entry.bind("<KeyRelease>", update_calculations)
divisor_entry.bind("<KeyRelease>", update_calculations)

app.mainloop()