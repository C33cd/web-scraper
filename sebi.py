# After reaching the Search Gazette options page:
page.locator("text=Search by Ministry").click()
page.wait_for_load_state("networkidle")

# After the form loads:
ministry_dropdown = page.locator("select").first
ministry_dropdown.wait_for(state="visible")
ministry_dropdown.select_option({"label": "Securities and Exchange Board of India"})
