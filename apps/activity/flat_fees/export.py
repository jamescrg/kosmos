import csv


def write_standard_csv(entries, response):
    writer = csv.writer(response)
    writer.writerow(
        [
            "Date",
            "Matter",
            "User",
            "Description",
            "Amount",
            "Comp",
            "Discounted Amount",
            "Entered",
            "Invoice",
        ]
    )
    for entry in entries:
        writer.writerow(
            [
                entry.date.strftime("%m/%d/%Y"),
                entry.matter.name,
                entry.user.initials if entry.user else "",
                entry.description,
                entry.amount,
                entry.comp,
                entry.discounted_amount,
                entry.entered,
                entry.invoice,
            ]
        )
    return response
