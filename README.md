# AutoTest_SmartTiming

This tool is designed for working out of time automatically from trace in XML format.

It parses trace formatted with xml and gets time stamp from the trace by locating related tag. Then it works out the final time and write the result into time_result.txt follwing along with name of trace. User should put trace into "trace" folder and the tool matchs the trace with function related to calculate the time. It also can get average time if needed.

Besides, the tool records the running log into smart_timing.log according to configuration of logging.yaml. User can find detail information about the working procedure from the log and take an effecient action to solve problems if cannot get time result.

User can run smart_timing.exe in adminstration mode directly out of python environment as smart_timing.py was packed into executed file with cxfreeze.
