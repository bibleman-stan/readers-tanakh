"""Quick test cases for poetic_register module. Run: py -3 test_poetic_register.py"""
from poetic_register import (
    is_sifrei_emet_chapter,
    is_embedded_poetry,
    is_acrostic_chapter,
    is_poetic_register,
)

def check(name, actual, expected):
    status = "PASS" if actual == expected else "FAIL"
    print(f"  [{status}] {name}: got {actual}, expected {expected}")

# Sifrei Emet
print("Sifrei Emet routing:")
check("psalms 1", is_sifrei_emet_chapter("psalms", 1), True)
check("psalms 150", is_sifrei_emet_chapter("psalms", 150), True)
check("proverbs 31", is_sifrei_emet_chapter("proverbs", 31), True)
check("job 1", is_sifrei_emet_chapter("job", 1), False)
check("job 3", is_sifrei_emet_chapter("job", 3), True)
check("job 42", is_sifrei_emet_chapter("job", 42), True)
check("jonah 1", is_sifrei_emet_chapter("jonah", 1), False)
check("jonah 2", is_sifrei_emet_chapter("jonah", 2), True)
check("genesis 1", is_sifrei_emet_chapter("genesis", 1), False)
check("01-genesis 1 (filename)", is_sifrei_emet_chapter("01-genesis", 1), False)

# Embedded poetry
print("Embedded poetry:")
check("exodus 15", is_embedded_poetry("exodus", 15), True)
check("exodus 14", is_embedded_poetry("exodus", 14), False)
check("deuteronomy 32", is_embedded_poetry("deuteronomy", 32), True)
check("deuteronomy 33 v2", is_embedded_poetry("deuteronomy", 33, 2), True)
check("deuteronomy 33 v29", is_embedded_poetry("deuteronomy", 33, 29), True)
check("deuteronomy 33 v1", is_embedded_poetry("deuteronomy", 33, 1), False)
check("judges 5", is_embedded_poetry("judges", 5), True)
check("1samuel 2 v5", is_embedded_poetry("1samuel", 2, 5), True)
check("1samuel 2 v15", is_embedded_poetry("1samuel", 2, 15), False)
check("habakkuk 3", is_embedded_poetry("habakkuk", 3), True)
check("lamentations 1", is_embedded_poetry("lamentations", 1), True)
check("songofsongs 8", is_embedded_poetry("songofsongs", 8), True)
check("ecclesiastes 3 v3", is_embedded_poetry("ecclesiastes", 3, 3), True)
check("ecclesiastes 3 v15", is_embedded_poetry("ecclesiastes", 3, 15), False)

# Acrostic
print("Acrostic chapters:")
check("psalms 119", is_acrostic_chapter("psalms", 119), True)
check("psalms 100", is_acrostic_chapter("psalms", 100), False)
check("lamentations 3", is_acrostic_chapter("lamentations", 3), True)
check("lamentations 5", is_acrostic_chapter("lamentations", 5), False)
check("proverbs 31 v15", is_acrostic_chapter("proverbs", 31, 15), True)
check("proverbs 31 v5", is_acrostic_chapter("proverbs", 31, 5), False)

# Convenience
print("Convenience is_poetic_register:")
check("genesis 1", is_poetic_register("genesis", 1), False)
check("psalms 23", is_poetic_register("psalms", 23), True)
check("exodus 15", is_poetic_register("exodus", 15), True)
check("deuteronomy 33 v26", is_poetic_register("deuteronomy", 33, 26), True)
check("lamentations 3 v25", is_poetic_register("lamentations", 3, 25), True)
check("proverbs 25 v11", is_poetic_register("proverbs", 25, 11), True)  # via Sifrei Emet
