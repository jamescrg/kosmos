import re

# --- T.6 Case Name Abbreviations (Bluebook Rule 10.2.1 & Table T.6) ---
# These are specifically for case names, not document titles
CASE_NAME_ABBREVIATIONS = {
    # Common words (T.6)
    "administration": "Admin.",
    "administrative": "Admin.",
    "administrator": "Adm'r",
    "america": "Am.",
    "american": "Am.",
    "association": "Ass'n",
    "authority": "Auth.",
    "automobile": "Auto.",
    "automotive": "Auto.",
    "board": "Bd.",
    "brother": "Bro.",
    "brothers": "Bros.",
    "building": "Bldg.",
    "business": "Bus.",
    "center": "Ctr.",
    "central": "Cent.",
    "chemical": "Chem.",
    "commission": "Comm'n",
    "commissioner": "Comm'r",
    "committee": "Comm.",
    "communications": "Commc'ns",
    "community": "Cmty.",
    "company": "Co.",
    "consolidated": "Consol.",
    "construction": "Constr.",
    "cooperative": "Coop.",
    "corporation": "Corp.",
    "county": "Cnty.",
    "department": "Dep't",
    "development": "Dev.",
    "director": "Dir.",
    "distribution": "Distrib.",
    "distributor": "Distrib.",
    "district": "Dist.",
    "division": "Div.",
    "eastern": "E.",
    "education": "Educ.",
    "educational": "Educ.",
    "electric": "Elec.",
    "electrical": "Elec.",
    "engineering": "Eng'g",
    "enterprise": "Enter.",
    "enterprises": "Enters.",
    "entertainment": "Ent.",
    "environment": "Env't",
    "environmental": "Envtl.",
    "equipment": "Equip.",
    "exchange": "Exch.",
    "executor": "Ex'r",
    "federal": "Fed.",
    "federation": "Fed'n",
    "financial": "Fin.",
    "foundation": "Found.",
    "general": "Gen.",
    "government": "Gov't",
    "guaranty": "Guar.",
    "hospital": "Hosp.",
    "incorporated": "Inc.",
    "indemnity": "Indem.",
    "independent": "Indep.",
    "industrial": "Indus.",
    "industries": "Indus.",
    "industry": "Indus.",
    "information": "Info.",
    "institute": "Inst.",
    "institution": "Inst.",
    "insurance": "Ins.",
    "international": "Int'l",
    "investment": "Inv.",
    "laboratory": "Lab.",
    "laboratories": "Labs.",
    "liability": "Liab.",
    "limited": "Ltd.",
    "litigation": "Litig.",
    "machine": "Mach.",
    "machinery": "Mach.",
    "maintenance": "Maint.",
    "management": "Mgmt.",
    "manufacturing": "Mfg.",
    "marketing": "Mktg.",
    "mechanical": "Mech.",
    "medical": "Med.",
    "memorial": "Mem'l",
    "metropolitan": "Metro.",
    "mortgage": "Mortg.",
    "municipal": "Mun.",
    "mutual": "Mut.",
    "national": "Nat'l",
    "northern": "N.",
    "number": "No.",
    "organization": "Org.",
    "partnership": "P'ship",
    "pharmaceutical": "Pharm.",
    "products": "Prods.",
    "production": "Prod.",
    "professional": "Prof'l",
    "property": "Prop.",
    "protection": "Prot.",
    "public": "Pub.",
    "publication": "Publ'n",
    "publishing": "Publ'g",
    "railroad": "R.R.",
    "railway": "Ry.",
    "regional": "Reg'l",
    "republic": "Rep.",
    "research": "Rsch.",
    "resource": "Res.",
    "resources": "Res.",
    "restaurant": "Rest.",
    "savings": "Sav.",
    "school": "Sch.",
    "science": "Sci.",
    "secretary": "Sec'y",
    "securities": "Sec.",
    "security": "Sec.",
    "service": "Serv.",
    "services": "Servs.",
    "society": "Soc'y",
    "southern": "S.",
    "southwest": "Sw.",
    "southwestern": "Sw.",
    "state": "St.",
    "steamship": "S.S.",
    "subcommittee": "Subcomm.",
    "superintendent": "Supt.",
    "surety": "Sur.",
    "system": "Sys.",
    "systems": "Sys.",
    "technical": "Tech.",
    "technology": "Tech.",
    "telecommunication": "Telecomm.",
    "telecommunications": "Telecomms.",
    "telephone": "Tel.",
    "television": "T.V.",
    "township": "Twp.",
    "transcontinental": "Transcon.",
    "transport": "Transp.",
    "transportation": "Transp.",
    "trust": "Tr.",
    "trustee": "Tr.",
    "uniform": "Unif.",
    "united": "U.",
    "university": "Univ.",
    "western": "W.",
}

# Special multi-word replacements for case names
CASE_NAME_SPECIAL = {
    "united states": "U.S.",
}


def abbreviate_case_name(case_name: str) -> str:
    """
    Abbreviate a case name according to Bluebook Rule 10.2.1 and Table T.6.

    Args:
        case_name: Full case name (e.g., "United States v. International Business
                   Machines Corporation")

    Returns:
        Abbreviated case name (e.g., "U.S. v. Int'l Bus. Machs. Corp.")
    """
    if not case_name:
        return ""

    # Handle special multi-word replacements first
    result = case_name
    for phrase, abbrev in CASE_NAME_SPECIAL.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        result = pattern.sub(abbrev, result)

    # Split by "v." to handle each party separately
    if " v. " in result:
        parts = result.split(" v. ", 1)
        abbreviated_parts = [_abbreviate_party_name(p.strip()) for p in parts]
        return " v. ".join(abbreviated_parts)
    else:
        return _abbreviate_party_name(result)


def _abbreviate_party_name(name: str) -> str:
    """Abbreviate a single party name."""
    words = name.split()
    result_words = []

    for i, word in enumerate(words):
        # Strip punctuation for lookup but preserve it
        clean_word = re.sub(r"[,.]$", "", word)
        trailing_punct = word[len(clean_word) :] if len(word) > len(clean_word) else ""

        # Check for abbreviation (case-insensitive)
        lower_word = clean_word.lower()
        if lower_word in CASE_NAME_ABBREVIATIONS:
            result_words.append(CASE_NAME_ABBREVIATIONS[lower_word] + trailing_punct)
        else:
            result_words.append(word)

    return " ".join(result_words)


# --- Combined T.6 (Parties) & T.16 (Document Types) Abbreviation Map ---
# NOTE: The keys are lowercased for case-insensitive matching.
ABBREVIATION_MAP = {
    # T.6 Party/Institutional Indicators frequently found in titles
    "plaintiff": "Pl.",
    "defendant": "Def.",
    "appellee": "Appellee",  # Keep spelled out to avoid ambiguity with App.
    "appellant": "Appellant",  # Keep spelled out to avoid ambiguity with App.
    "corporation": "Corp.",
    "incorporated": "Inc.",
    "association": "Ass'n",
    "company": "Co.",
    "limited": "Ltd.",
    # T.16 Document Types and Subdivisions
    "affidavit": "Aff.",
    "amendment": "Amend.",
    "answer": "Answer",  # T.16 lists 'Answer' as spelled out
    "appendix": "App.",
    "article": "Art.",
    "brief": "Br.",
    "certificate": "Cert.",
    "claim": "Claim",
    "complaint": "Compl.",
    "declaration": "Decl.",
    "deposition": "Dep.",
    "exhibit": "Ex.",
    "interrogatories": "Interrog.",
    "interrogatory": "Interrog.",
    "memorandum": "Mem.",
    "motion": "Mot.",
    "opposition": "Opp'n",
    "paragraph": "Para.",
    "petition": "Pet.",
    "record": "R.",
    "reply": "Reply",
    "request": "Req.",
    "response": "Resp.",
    "section": "§",
    "stipulation": "Stip.",
    "subpoena": "Subp.",
    "summary": "Summ.",
    "supplement": "Supp.",
    "transcript": "Tr.",
    "volume": "Vol.",
    # Common T.6/T.13 words often used in titles
    "judgment": "J.",
    "law": "L.",
    "letter": "Ltr.",
    "order": "Order",  # Often not abbreviated
}

# --- Connecting Words to Omit (Rule 10.2.1(a)) ---
# These words are generally not abbreviated or are omitted entirely.
SHORT_WORDS_TO_OMIT = {"for", "the", "of", "and", "in", "on", "a"}


def bluebook_abbreviate(title: str) -> str:
    """
    Abbreviates words in a court document title according to The Bluebook Rules
    (primarily T.16 for document types and Rule 10.2.1 for omissions).

    Args:
        title: The full title of the court document (e.g., "Plaintiff's Motion
               for Summary Judgment and Incorporated Memorandum of Law").

    Returns:
        The abbreviated document title string (e.g., "Pl.'s Mot. Summ. J.
        & Inc. Mem. L.").
    """
    # 1. Split the title by spaces, while preserving separators and punctuation
    # This regex attempts to find words, numbers, and common punctuation/separators
    words = re.findall(r"[\w.'&/]+|v\.|et al\.|,|;", title)

    abbreviated_words = []

    # Track the first word for the "first word not abbreviated" rule.
    is_first_word = True

    for word in words:
        # Check for possessive and strip it for lookup
        is_possessive = word.lower().endswith("'s")
        if is_possessive:
            base_word = re.sub(r"'s$", "", word, flags=re.IGNORECASE).lower()
        else:
            base_word = re.sub(r"['.]*$", "", word).lower()

        # --- Rule 10.2.2: Omit short connecting words ---
        if base_word in SHORT_WORDS_TO_OMIT:
            # Rule 10.2.1(a) requires 'and' to be replaced by '&' if not first word
            if base_word == "and" and not is_first_word:
                abbreviated_words.append("&")
            # Otherwise, skip 'for', 'the', 'of', 'in', 'on', 'a'
            continue

        # --- Rule 10.2.2: Do not abbreviate the first word ---
        # if is_first_word:
        #     abbreviated_words.append(word)
        #     is_first_word = False
        #     continue

        # --- Rule 10.2.2 & T.16: Apply specific abbreviations ---
        if base_word in ABBREVIATION_MAP:
            abbreviated_word = ABBREVIATION_MAP[base_word]

            # Handle possessives (e.g., Plaintiff's -> Pl.'s)
            if is_possessive:
                if abbreviated_word.endswith("."):
                    abbreviated_word = abbreviated_word[:-1] + "'s"
                else:
                    abbreviated_word = abbreviated_word + "'s"

            abbreviated_words.append(abbreviated_word)

        # --- Catchall: Abbreviate words of 8 letters or more to 3 letters ---
        elif len(base_word) >= 8:
            # Abbreviate to first 3 letters, capitalized, with period
            abbreviated_word = base_word[:3].capitalize() + "."
            if is_possessive:
                abbreviated_word = abbreviated_word[:-1] + "'s"
            abbreviated_words.append(abbreviated_word)

        # --- No abbreviation needed (proper nouns, non-T.6/T.16 words < 8 letters) ---
        else:
            abbreviated_words.append(word)

    # 2. Join the words back into a single string
    result = " ".join(abbreviated_words)

    # 3. Clean up spacing before punctuation and specific terms
    result = re.sub(r"\s([,.;&])", r"\1", result)
    result = re.sub(r" '\s", "'", result)
    return result
