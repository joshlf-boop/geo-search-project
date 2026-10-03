"""
GEO Caner Dataset Catalog

Searches NCBI GEO for cancer-related studies, retrieves study and
 sample-level metadata, parses relevant experimental information, 
 and exports the result to CSV files for downstream analysis
"""



from Bio import Entrez
import csv
import urllib.request

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

def get_sample_metadata(gsm_accession):
    url = (
        "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
        f"?acc={gsm_accession}&targ=self&form=text&view=full"
    )

    with urllib.request.urlopen(url) as response:
        sample_data = response.read().decode("utf-8")

    return sample_data

def parse_sample_metadata(sample_data):
    sample_info = {
        "source": "Not available",
        "organism": "Not available",
        "preservation_method": "Not available",
        "cell_line": "Not available",
        "genotype": "Not available",
        "treatment": "Not available",
        "rna_type": "Not available",
        "library_strategy": "Not available",
        "instrument": "Not available"
    }

    for line in sample_data.splitlines():

        if line.startswith("!Sample_source_name_ch1 ="):
            sample_info["source"] = line.split("=", 1)[1].strip()

        elif line.startswith("!Sample_organism_ch1 ="):
            sample_info["organism"] = line.split("=", 1)[1].strip()

        elif line.startswith("!Sample_characteristics_ch1 ="):
            value = line.split("=", 1)[1].strip()

            if value.startswith("cell line:"):
                sample_info["cell_line"] = value.split(":", 1)[1].strip()

            elif value.startswith("genotype:"):
                sample_info["genotype"] = value.split(":", 1)[1].strip()

            elif value.startswith("tissue preservation method:"):
                sample_info["preservation_method"] = value.split(":", 1)[1].strip()

        elif line.startswith("!Sample_molecule_ch1 ="):
            sample_info["rna_type"] = line.split("=", 1)[1].strip()

        elif line.startswith("!Sample_treatment_protocol_ch1 ="):
            sample_info["treatment"] = line.split("=", 1)[1].strip()

        elif line.startswith("!Sample_library_strategy ="):
            sample_info["library_strategy"] = line.split("=", 1)[1].strip()

        elif line.startswith("!Sample_instrument_model ="):
            sample_info["instrument"] = line.split("=", 1)[1].strip()

    return sample_info

def get_all_sample_metadata(study):
    parsed_samples = []

    for sample in study.get("Samples", []):
        accession = sample.get("Accession")

        if not accession:
            continue

        raw_metadata = get_sample_metadata(accession)
        parsed_metadata = parse_sample_metadata(raw_metadata)

        parsed_metadata["study_accession"] = study.get("Accession", "Not available")
        parsed_metadata["accession"] = accession
        parsed_metadata["title"] = sample.get("Title", "Not available")

        parsed_samples.append(parsed_metadata)

    return parsed_samples

def organize_studies(summaries, disease):
    organized_studies = []

    for study in summaries:
        sample_list = study.get("Samples", [])

        sample_titles = []

        for sample in sample_list:
            sample_titles.append(sample.get("Title", "Not available"))

        study_info = {
            "disease": disease,
            "title": study.get("title", "Not available"),
            "accession": study.get("Accession", "Not available"),
            "samples": int(study.get("n_samples", 0)),
            "data_type": study.get("gdsType", "Not available"),
            "sample_titles": "; ".join(sample_titles),
            "conditions": "",
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
        "data_type",
        "sample_titles",
        "conditions",
        "summary",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(studies)

def save_samples_to_csv(samples, filename):
    if not samples:
        return

    fieldnames = [
        "study_accession",
        "accession",
        "title",
        "source",
        "organism",
        "preservation_method",
        "cell_line",
        "genotype",
        "treatment",
        "rna_type",
        "library_strategy",
        "instrument",
    ]

    rows = []

    for sample in samples:

        row = {}

        for field in fieldnames:
            row[field] = sample.get(field, "Not available")

        rows.append(row)

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)



disease = input("Enter a disease to search GEO: ")

results = search_geo(disease)
summaries = get_geo_summaries(results)


studies = organize_studies(summaries, disease)

save_to_csv(studies, "geo_studies.csv")

print(f"Saved {len(studies)} studies to geo_studides.csv")

print("\nParsing samples from all studies...")

all_samples = []

for study in summaries:
    study_accession = study.get("Accession", "Not available")

    print(f"Parsing {study_accession}...")

    samples = get_all_sample_metadata(study)
    all_samples.extend(samples)

print(f"\nParsed {len(all_samples)} total samples.")
save_samples_to_csv(all_samples, "sample_metadata.csv")

print("Saved sample metadata to sample_metadata.csv")
