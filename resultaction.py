import subprocess


class ResultAction:
    def __init__(self, action_type, name, arg):
        self.action_type = action_type
        if self.action_type == "eval":
            self.name = eval(arg)
        else:
            self.name = name
        self.arg = arg

    def do_action(self, arg=None):
        if self.action_type == "eval":
            # copy result to clipboard
            return self.name
        else:
            target = arg
            if not target:
                target = self.path
            subprocess.call(["open", target])
            return None
