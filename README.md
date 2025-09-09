## Environment setup
To get started, create a python environment with the given requirements.txt file as follows:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Code organization
There are 3 main modules.

### synthetic_lead_generator.py
This module contains the GrokDataGenerator class that uses Grok-4 to generate synthetic leads data. The data is structured consistent with the schema that is contained in the `lead_management.py` file. This module is used to generate `count` number of leads. Further customization of the leads is possible by setting the `quality_context` (not shown in the demo example)

### lead_management.py
This module defines the data structure for what a lead looks like. It contains various functions to add, delete, edit, find and update leads with various attributes. The `qualify_lead` function creates scores for each lead based on various factors like the company size, budget, authority of decision making, need / painpoints, and timeline. This module further classifies the leads as `qualified` or `unqualified`. The `create_lead_objects_from_data` module converts synthetically generated leads data to the Lead class and scores them. This module returns a list of the scored lead IDs.

### chat_interface.py
This module contains the `GROK_CLI` class to interact with the leads data through the command line. Typing `help` at the CLI shows various options for the user to interact with the data. For simple quantifications or classifications of the leads, the module calls locally defined functions within the `LeadManager`. For more complex queries that use the conversation history, the chat module invokes Grok-4 to present the response to the user.

### main.py
This function strings together the modules in the following order:
1. Synthetic data generation (count specificed in `NUM_LEADS` at the top)
2. Conversion of the synthetic leads to `Lead` objects via `create_lead_objects_from_data`
3. Chatting with the data via `run_interactive_session` in a loop until the user chooses to exit.
