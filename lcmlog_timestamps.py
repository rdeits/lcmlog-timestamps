import lcm
import inspect


def lcmtype_classes(module):
    return [c[1] for c in inspect.getmembers(module) if inspect.isclass(c[1]) and hasattr(c[1], "_get_packed_fingerprint")]

def fingerprint_map(classes):
    return {c._get_packed_fingerprint(): c for c in classes}

class MessageTypeManager(object):
    def __init__(self, lcmtype_module_names):
        self.fingerprint_to_type = {}
        for name in lcmtype_module_names:
            try:
                module = __import__(name)
                self.fingerprint_to_type.update(fingerprint_map(lcmtype_classes(module)))
            except ImportError:
                print "Warning: could not import module {:s}".format(name)

    def get_message_type(self, event):
        fingerprint = event.data[:8]
        try:
            return self.fingerprint_to_type[fingerprint]
        except KeyError:
            raise ValueError("Could not find fingerprint to match event on channel: {:s}".format(event.channel))

    def decode_event(self, event):
        msg_type = self.get_message_type(event)
        return msg_type.decode(event.data)

def replace_timestamps_with_log_times(manager, input_log, output_log, overwrite=False):
    if not isinstance(input_log, lcm.EventLog):
        input_log = lcm.EventLog(input_log, "r")
    if not isinstance(output_log, lcm.EventLog):
        output_log = lcm.EventLog(output_log, "w", overwrite=overwrite)
    for event in input_log:
        msg = manager.decode_event(event)
        for field in ["utime", "timestamp"]:
            if hasattr(msg, field):
                setattr(msg, field, event.timestamp)
                break
        output_log.write_event(event.timestamp, event.channel, msg.encode())

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Replace the utime or timestamp field of all LCM messages in a log with the timestamp recorded by the lcm-logger process")
    parser.add_argument('source', type=str, help="source log file")
    parser.add_argument('destination', type=str, help="destination log file (will be overwritten if necessary)")
    parser.add_argument('lcmtype_module_names', type=str, nargs='+', help="names of python modules containing lcm type definitions")
    args = parser.parse_args()
    print args.lcmtype_module_names
    manager = MessageTypeManager(args.lcmtype_module_names)
    replace_timestamps_with_log_times(manager, args.source, args.destination, overwrite=True)
