# [FEATURE]Add native FrappeTool for ERPNext and Frappe Framework integration

**Issue #4657** | State: open | Created: 2026-03-01 | Updated: 2026-03-09
**Author:** SathwikGuduguntla
**Labels:** feature-request

### Feature Area

Integration with external tools

### Is your feature request related to a an existing bug? Please link it here.

NA

### Describe the solution you'd like

I would like to see a native @frappe added to the crewai-tools library. This tool will allow agents to interact with any site running on the Frappe Framework or ERPNext via its REST API.

The tool should support:

get_doc: Fetching complete details of a specific DocType record.

get_list: Searching for records using standard Frappe filters.

create_doc / update_doc: Enabling agents to log new data or update existing statuses in the ERP.

execute_method: Triggering whitelisted server-side functions for complex business logic.

Proposed Parameters:

site_url: The base URL of the site.

api_key: For secure authentication.

api_secret: For secure authentication.

This integration will enable autonomous agents to manage real-world enterprise workflows, such as inventory updates, HR tasks, or specialised industry apps

### Describe alternatives you've considered

_No response_

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**spider-yamet:**
Can I work on this issue, @greysonlalonde @joaomdmoura ?

Hope this project is open for contribution

**SathwikGuduguntla:**
@spider-yamet I have opened this issue and I’m currently working on it. Could you please look into another issue instead? Thank you
