import csv

def filter_csv_by_addresses(source_csv, filter_csv, output_csv):
    # Read the addresses from the source CSV
    with open(source_csv, mode='r', newline='') as file:
        csv_reader = csv.DictReader(file)
        addresses = {row['user_address'] for row in csv_reader}

    # Filter the second CSV by these addresses
    with open(filter_csv, mode='r', newline='') as infile, open(output_csv, mode='w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)

        # Write the header to the output CSV
        writer.writeheader()

        # Write only the rows with addresses that are in the source CSV
        for row in reader:
            if row['Address'] in addresses:
                writer.writerow(row)
                row[""]


from decimal import Decimal

def sum_degen_values(csv_file):
    total_degen = Decimal('0')
    
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        
        # Sum up all the 'bridged degen value' from each row
        for row in reader:
            if row['bridged degen value']:
                total_degen += Decimal(row['bridged degen value'])
                
    return total_degen, total_degen / Decimal(10) ** 18

print(sum_degen_values("degen_bridged_by_swappers.csv"))