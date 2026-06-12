def extract_segment(text, segment_id):
    """
    Finds all EDI segments starting with a specific segment ID.
    """
    segments = text.replace("\n", "").replace("\r", "").split("~")
    segments = [seg.strip() for seg in segments]
    return [seg for seg in segments if seg.startswith(segment_id + "*")]


def get_denial_type(carc_code):
    mapping = {
        "50": "Medical Necessity",
        "197": "Authorization",
        "16": "Missing Information",
        "18": "Duplicate Claim",
        "22": "Coordination of Benefits",
        "29": "Timely Filing",
        "96": "Non-Covered Service",
        "109": "Eligibility",
        "11": "Diagnosis Inconsistent",
        "97": "Bundled Service",
        "250": "Contractual / Policy Adjustment",
        "45": "Charge Exceeds Fee Schedule",
    }
    return mapping.get(str(carc_code), "General Denial")


def get_assigned_team(denial_type):
    routing = {
        "Medical Necessity": "Clinical Appeals Team",
        "Authorization": "Authorization Team",
        "Missing Information": "Documentation Team",
        "Duplicate Claim": "Billing Review Team",
        "Coordination of Benefits": "Registration Team",
        "Timely Filing": "Billing Review Team",
        "Non-Covered Service": "Clinical Appeals Team",
        "Eligibility": "Registration Team",
        "Diagnosis Inconsistent": "Coding Team",
        "Bundled Service": "Coding Team",
        "Contractual / Policy Adjustment": "Billing Review Team",
        "Charge Exceeds Fee Schedule": "Billing Review Team",
        "General Denial": "Billing Review Team",
    }
    return routing.get(denial_type, "Billing Review Team")


def get_recommended_action(denial_type):
    actions = {
        "Medical Necessity": "Review physician documentation and submit supporting clinical evidence.",
        "Authorization": "Verify authorization status and attach missing prior authorization documentation.",
        "Missing Information": "Review claim for missing required documentation and resubmit corrected claim.",
        "Duplicate Claim": "Validate whether the claim was previously submitted or paid before resubmission.",
        "Coordination of Benefits": "Confirm primary and secondary payer responsibility before resubmission.",
        "Timely Filing": "Review filing deadline and submit appeal with proof of timely submission if available.",
        "Non-Covered Service": "Review patient benefits and payer policy before appeal or patient billing.",
        "Eligibility": "Verify patient coverage and eligibility for the date of service.",
        "Diagnosis Inconsistent": "Review diagnosis and procedure code alignment before correction.",
        "Bundled Service": "Review coding rules and determine whether separate payment is allowed.",
        "Contractual / Policy Adjustment": "Review payer contract terms and determine whether adjustment is appealable.",
        "Charge Exceeds Fee Schedule": "Review allowed amount and payer fee schedule for accuracy.",
        "General Denial": "Review claim details, payer response, and supporting documentation.",
    }
    return actions.get(denial_type, "Review claim details and supporting documentation.")


def parse_835_file(file_content):
    """
    Demo-level parser for 835 EDI claim denial files.
    """

    text = file_content.replace("\r", "").replace("\n", "")

    # Payer name from N1*PR
    payer = "Unknown Payer"
    for seg in extract_segment(text, "N1"):
        parts = seg.split("*")
        if len(parts) > 2 and parts[1] == "PR":
            payer = parts[2].title()
            break

    # Patient name from NM1*QC
    patient_name = "Unknown Patient"
    for seg in extract_segment(text, "NM1"):
        parts = seg.split("*")
        if len(parts) > 4 and parts[1] == "QC":
            last_name = parts[3].title()
            first_name = parts[4].title()
            patient_name = f"{first_name} {last_name}".strip()
            break

    # Claim details from CLP
    claim_id = "Unknown Claim"
    billed_amount = 0.0
    paid_amount = 0.0
    denied_amount = 0.0

    clp_segments = extract_segment(text, "CLP")
    if clp_segments:
        parts = clp_segments[0].split("*")
        if len(parts) > 5:
            claim_id = parts[1]
            billed_amount = float(parts[3])
            paid_amount = float(parts[4])
            denied_amount = float(parts[5])

    # CARC code from first CAS segment
    carc_code = "Unknown"
    cas_segments = extract_segment(text, "CAS")
    if cas_segments:
        parts = cas_segments[0].split("*")
        if len(parts) > 2:
            carc_code = parts[2]

    # RARC from LQ*HE segment
    rarc_code = "Not Available"
    for seg in extract_segment(text, "LQ"):
        parts = seg.split("*")
        if len(parts) > 2 and parts[1] == "HE":
            rarc_code = parts[2]
            break

    denial_type = get_denial_type(carc_code)
    assigned_team = get_assigned_team(denial_type)
    recommended_action = get_recommended_action(denial_type)

    priority = "High" if denied_amount >= 3000 else "Medium" if denied_amount >= 1500 else "Low"

    return {
        "claim_id": claim_id,
        "patient_name": patient_name,
        "payer": payer,
        "denial_type": denial_type,
        "amount": denied_amount,
        "priority": priority,
        "assigned_team": assigned_team,
        "status": "New",
        "date_received": "2026-06-11",
        "potential_recovery": denied_amount,
        "carc_code": carc_code,
        "rarc_code": rarc_code,
        "recommended_action": recommended_action,
        "billed_amount": billed_amount,
        "paid_amount": paid_amount,
    }