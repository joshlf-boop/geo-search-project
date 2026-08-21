from Bio import Entrez
import csv

Entrez.email = "joshlf@umich.edu"

def search_geo(search_term):
    search_handle = Entrez.esearch(
        db="gds",
        term=search_term,
        retmax=20
    )

    search_results = Entrez.read(search_handle)

    search_handle.close()

    id_list = search_results["IdList"]

    return id_list

def get_geo_summaries(id_list):
    """Retrieve readable GEO summaries for a list of record IDs."""

    if not id_list:
        return []

    with Entrez.esummary(
        db="gds",
        id=",".join(id_list)

    ) as summary_handle:

        summary_results = Entrez.read(summary_handle)
    return summary_results
def organize_studies(summaries, disease):
    organized_studies = []

    for study in summaries:
        study_info = {
            "disease": disease,
            "title": study.get("title", "Not available"),
            "accession": study.get("Accession", "Not available"),
            "samples": study.get("n_samples", "Not available"),
            "study_type": study.get("gdsType", "Not available"),
            "summary": study.get("summary", "Not available")
        }

        organized_studies.append(study_info)
    return organized_studies

def save_to_csv(studies, filename):
    if not studies:
        return

    fieldnames = [
        "disease",
        "title",
        "accession",
        "samples",
        "study_type",
        "summary",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(studies)

disease = "liver cancer"

results = search_geo(disease)
summaries = get_geo_summaries(results)
studies = organize_studies(summaries, disease)

save_to_csv(studies, "geo_studies.csv")

print(f"Saved {len(studies)} studies to geo_studides.csv")