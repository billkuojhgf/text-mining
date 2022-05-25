from mask_module import ConcreteMaskMart
from mask_module import ConcreteMaskType
from mask_module import ConcreteRegexSearch
import pandas as pd

mask_mart = None


def mask():
    global mask_mart
    mask_mart = ConcreteMaskMart()

    # Create a new Observer called simple_mask
    simple_mask = ConcreteMaskType("Simple Mask")
    mask_mart.attach(simple_mask)

    # two regex contains in the simple mask_module
    simple_mask_flow_rate = ConcreteRegexSearch("flow rate", [
        r"s-m.*?(\d{1,2}) * l",
        r"sm.*?(\d{1,2})l\/(m)",
        r"s'm.*?(\d{1,2})l\/ min",
        r"simpo.*mask_module.*?(\d{1,2}) *?l\/min",
        r"s\/m.*(\d{1,2})(l ?(\/min)?[^a-z]|liter|lpm)",
        r"mask_module.*?(\d{1,2} *?l)",
    ])
    simple_mask.attach_search_regex(simple_mask_flow_rate)

    # Nasal Cannula
    nasal_cannula = ConcreteMaskType("Nasal Cannula")
    mask_mart.attach(nasal_cannula, 1)
    nasal_cannula_flow_rate = ConcreteRegexSearch("FiO2", [
        r"cannula.*?(\d{1,2}).{0,2}l ?(\/min)?",
        r"nasal.*(\d{1,2})[ _]{0,3}[^a-z]*(l ?(\/min)?[^a-z]|liter|lpm)",
        r"n\/c.*?(\d{1,2})l\/min",
        r"nc.*(\d{1,2}?l)/min",
    ])
    nasal_cannula.attach_search_regex(nasal_cannula_flow_rate)

    return mask_mart


if __name__ == '__main__':
    # here put your inpatient treatment text
    with open("./csv/15472_住院護理醫囑處置_1.csv", newline='') as csv_file:
        df = pd.read_csv(csv_file, encoding='utf-8')
        for row in df.iterrows():
            row = row[1]
            txt = str(row.處置項目)
            # txt = "MASK 10L/MIN->N/C 3L/MIN"
            result = mask_mart.treatment_mining(txt)
            if result:
                print('txt= {}, \nresult= {}'.format(txt, result))
                print("---------------------------")
    print("Done")
