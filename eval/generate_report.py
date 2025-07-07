import argparse
import yaml
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.style.use('https://github.com/taha-yassine/mplstyles/raw/master/styles/dark.mplstyle')

def create_radar_chart(labels, values, output_path):
    """Creates and saves a radar chart."""
    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

    values_closed = values + values[:1]
    angles_closed = angles + angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    ax.plot(angles_closed, values_closed)
    ax.fill(angles_closed, values_closed, alpha=0.07)

    ax.set_thetagrids(np.degrees(angles), labels)

    ax.set_rlabel_position(30)
    ax.set_yticks([20, 40, 60, 80])
    ax.set_yticklabels(["20%", "40%", "60%", "80%"])
    ax.set_ylim(0, 100)
    
    ax.set_title("Performance by Category", y=1.1)

    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Generate a report from model output.")
    parser.add_argument(
        "--model_output_dir",
        type=Path,
        required=True,
        help="Directory containing the model's output files.",
    )
    args = parser.parse_args()

    model_output_dir = args.model_output_dir
    figures_dir = model_output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)

    report_md_content = "# Model Performance Report\n\n"

    # Process reports.yaml for summary
    summary_report_file = model_output_dir / "reports.yaml"
    if summary_report_file.is_file():
        with open(summary_report_file, 'r') as f:
            summary_data = yaml.safe_load(f)
        
        report_md_content += "## Overall Performance\n\n"
        for item in summary_data:
            report_md_content += f"- **Model:** {item['model_id']}\n"
            report_md_content += f"  - **Success Rate:** {item['good_percent']}\n"
            report_md_content += f"  - **Confidence Interval:** {item['confidence_interval']}\n"
            report_md_content += f"  - **Good:** {item['good']}\n"
            report_md_content += f"  - **Total:** {item['total']}\n\n"
    else:
        print(f"Warning: {summary_report_file} not found.")

    # Process reports-by-category.yaml for radar chart
    category_report_file = model_output_dir / "reports-by-category.yaml"
    if category_report_file.is_file():
        with open(category_report_file, 'r') as f:
            category_data = yaml.safe_load(f)

        labels = [item['category'] for item in category_data]
        values = [float(item['good_percent'].strip('%')) for item in category_data]

        chart_path = figures_dir / "radar_chart.png"
        create_radar_chart(labels, values, chart_path)

        relative_chart_path = chart_path.relative_to(model_output_dir)
        
        report_md_content += "## Performance by Category\n\n"
        report_md_content += f"![Performance by Category](./{relative_chart_path})\n"
    else:
        print(f"Warning: {category_report_file} not found.")

    report_md_path = model_output_dir / "report.md"
    with open(report_md_path, 'w') as f:
        f.write(report_md_content)

    print(f"Report generated at {report_md_path}")


if __name__ == "__main__":
    main()
