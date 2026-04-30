def calculate_summary(entries):
    total_amount = 0
    comp_amount = 0
    admin_amount = 0

    for entry in entries:
        total_amount += entry.amount

        if entry.comp:
            comp_amount += entry.amount

        if hasattr(entry, "matter") and entry.matter and not entry.matter.billable:
            admin_amount += entry.amount

    net_amount = total_amount - comp_amount - admin_amount

    return {
        "total_amount": total_amount,
        "comp_amount": comp_amount,
        "admin_amount": admin_amount,
        "net_amount": net_amount,
    }
