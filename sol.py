import os
import requests
import yaml


API_KEY = "at_FXMPnB88jwZNs7rP90WFz9UYKr3kv"
URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
MAX_COLUMN_LEN = 15
MAX_HOSTNAMES_LEN = 25


extracted_domain_data = {
    "Domain Name": ["domainName"],
    "Registrar Name": ["createdDate"],
    "Registration Date": ["createdDate"],
    "Expiration Date": ["expiresDate"],
    "Estimated Domain Age": ["estimatedDomainAge"],
    "Hostnames": ["nameServers", "hostNames"]
}

extracted_contact_data = {
    "Registrant Name": ["registrant", "name"],
    "Technical Contact Name": ["technicalContact", "name"],
    "Administrative Contact Name": ["administrativeContact", "name"],
    "Contact Email": ["contactEmail"]
}


def write_dict_to_yaml_file(data: dict, file_name: str) -> str:
    """
    Create a YAML file and write the dictionary data to it.

    :param data: Dictionary to be written into the YAML file.
    :param file_name: Name of the YAML file to be created.
    :return: Status message indicating success or error.
    """
    try:
        with open(file_name, "w") as file:
            yaml.dump(data, file, default_flow_style=False)
        return f"YAML file '{file_name}' created successfully!"
    except Exception as e:
        return f"Error: {str(e)}"


def fetch_domain_info(domain: str) -> dict:
    """
    Fetch domain information from the WhoisXMLAPI.

    :param domain: The domain name to fetch information for.
    :return: JSON response from the API or an error message.
    """
    params = {
        "domainName": domain,
        "apiKey": API_KEY,
        "outputFormat": "JSON"
    }

    try:
        response = requests.get(URL, params=params)
        response.raise_for_status()
        return response.json()["WhoisRecord"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API request failed: {str(e)}")


def get_nested_value(data: dict, keys: list) -> str:
    """
    Retrieve a value from nested dictionary keys.

    :param data: Dictionary to retrieve the value from.
    :param keys: List of keys representing the path to the value.
    :return: Retrieved value or "N/A" if the keys are invalid.
    """
    try:
        current = data
        for key in keys[:-1]:
            current = current[key]

        if keys[-1] == "name" and isinstance(current, dict):
            return current.get("name") or current.get("organization") or "N/A"

        return current[keys[-1]] if keys[-1] in current else "N/A"

    except Exception as e:
        print(f"Error accessing data: {e}")
        return "N/A"


def generate_markdown_table(data: dict, extracted_data: dict) -> str:
    """
    Generate a Markdown table from a dictionary of data.

    :param data: Dictionary containing the data to display in the table.
    :param extracted_data: Mapping of table fields to their respective keys in the data.
    :return: Generated Markdown table as a string.
    """
    headers = list(extracted_data.keys())
    values = []

    for field, keys in extracted_data.items():
        val = get_nested_value(data, keys)

        if field == "Hostnames":
            val = ", ".join(val)
            if len(val) > MAX_HOSTNAMES_LEN:
                val = val[:MAX_HOSTNAMES_LEN] + "..."
        values.append(val)

    lens = [max(len(header), len(str(val))) for header, val in zip(headers, values)]
    header_row = f"| {' | '.join(header.ljust(lens[i]) for i, header in enumerate(headers))} |"
    separator_row = f"| {' | '.join('-' * lens[i] for i in range(len(headers)))} |"
    data_row = f"| {' | '.join(str(values[i]).ljust(lens[i]) for i in range(len(values)))} |"
    table = f"{header_row}\n{separator_row}\n{data_row}"
    return table


def add_table_to_md_file(file_path: str, table: str, header: str = None) -> None:
    """
    Append a Markdown table to a .md file, with an optional header.

    :param file_path: Path of the Markdown file to append to.
    :param table: Markdown table to append.
    :param header: Optional header to add before the table.
    :return: None
    """
    mode = 'a' if os.path.exists(file_path) else 'w'
    with open(file_path, mode, encoding='utf-8') as md_file:
        if header:
            md_file.write(f"{header}\n\n")
        md_file.write(f"{table}\n\n")
        print(f"Table added to '{file_path}' successfully.")


def main_func(domain: str) -> tuple[str, str]:
    """
    Return tables instead of writing to file directly for better flexibility
    :param domain: The domain name to fetch information for.
    :return: contact table and domain table
    """
    try:
        whois_data = fetch_domain_info(domain)
        domain_table = generate_markdown_table(whois_data, extracted_domain_data)
        contact_table = generate_markdown_table(whois_data, extracted_contact_data)
        file_name = f"{domain.split(".")[0]}_information.md"
        add_table_to_md_file(table=domain_table, file_path=file_name, header="Domain Information")
        add_table_to_md_file(table=contact_table, file_path=file_name, header="Contact Information")
        return domain_table, contact_table
    except Exception as e:
        raise RuntimeError(f"Failed to process domain {domain}: {str(e)}")


if __name__ == "__main__":
    domain = "chatgpt.com"
    main_func(domain=domain)
