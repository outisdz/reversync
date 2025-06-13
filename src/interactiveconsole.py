import pyfiglet
from blessed import Terminal
from rich import print as rprint
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich import box
import readline


BOLD = "\033[1m"
GREEN = "\033[32m"
RESET = "\033[0m"
RED = "\033[31m"

class InteractiveConsole:
    """
    A terminal-based interactive shell for a reverse shell server interface.
    Provides input handling, output rendering, and styled interface using 'blessed' and 'rich'.
    """
    def __init__(self,logo):
        """Initialize terminal, buffers, and default shell_prompt."""
        # font: amc_aaa01
        # font: ansi_regular
        # font: ansi_shadow
        # font: roman
        print('\n'+f'{GREEN}{BOLD}' + pyfiglet.figlet_format("rever\n sync".upper(),font="amc_aaa01") + f'{logo}' + f'{RESET}'+'\n')

        self._term = Terminal()
        self._error_buffer = []                     # Stores error messages
        self._output_buffer = []                    # Stores printed messages
        self._input_buffer = []                     # Stores currently typed characters
        self.shell_prompt = '@remote-shell > '      # Default prompt label
        self.run = True                             # Controls the main input loop
        self._index = 1


    @property
    def output(self):
        """Expose the output buffer."""
        return  self._output_buffer

    @output.setter
    def output(self,data):
        """
        Add a message to the output buffer and render it.
        :param data: String message to display in the terminal
        """
        self._output_buffer.append(data)
        self.print()

    @property
    def error(self):
        """Expose the error buffer."""
        return self._error_buffer

    @error.setter
    def error(self,data):
        """
        Add a message to the error buffer and render it.
        :param data: String message to display in the terminal
        """
        self._error_buffer.append(data)
        self.print()

    def b_input(self):
        """
        Main user input loop. Reads characters with basic handling for backspace and enter.
        :return: The final string input when the user presses Enter
        """
        with self._term.cbreak():
            while self.run:
                self.print()
                # Non-blocking key read: waits 0.1s for input, then continues if no key is pressed
                key = self._term.inkey(0.1)
                if not key:
                    continue
                if key.name == 'KEY_UP':
                    seq = readline.get_history_item(self._index)
                    if seq:
                        self._input_buffer = list(seq)
                        self._index=min(self._index+1,readline.get_current_history_length())
                    continue
                if key.name == 'KEY_LEFT':
                    continue
                if key.name == 'KEY_RIGHT':
                    continue
                if key.name == 'KEY_DOWN':
                    seq = readline.get_history_item(self._index)
                    if seq:
                        self._input_buffer = list(seq)
                        self._index=max(1,self._index-1)
                    else:
                        self._input_buffer.clear()
                    continue
                if key.name == 'KEY_BACKSPACE':
                    if self._input_buffer:
                        self._input_buffer.pop()
                        self.print()
                    continue
                if key.name == "KEY_ENTER":
                    data = ''.join(self._input_buffer)
                    if not data:
                        continue
                    self._input_buffer.clear()
                    self.print_input(data)
                    for _ in range(1,readline.get_current_history_length()):
                        if data.strip() == readline.get_history_item(_).strip():
                            return data
                    readline.add_history(data)
                    return data
                if key.isprintable():
                    self._input_buffer.append(key)
            return ''

    def print_input(self,data:str):
        # Build the prompt + input line
        self._index = 1
        prompt = Text()
        prompt.append(f"{self.shell_prompt}", style="bold red")
        prompt.append(''.join(data), style="white")
        print(self._term.clear_bol + self._term.move_x(0), end='', flush=True)
        rprint(Panel(
            prompt,
            border_style="bold green",
            padding=(0, 1),
            expand=True,
            box=box.ASCII2
        ),
            flush=True)

    def print(self):
        """
        Render all buffered output messages in styled panels.
        Also reprints the current shell prompt and partially typed command.
        """
        # Clear current line and render each output panel
        print(self._term.clear_bol + self._term.move_x(0), end='', flush=True)
        if self.output:
            for m in  self._output_buffer:
                panel_text = Text(m, style=Style(color="white"))
                rprint(Panel(
                    panel_text,
                    title=f"Server Output [red bold]{self.shell_prompt}[/red bold]",
                    title_align="left",
                    border_style="bold blue",
                    padding=(0, 1),
                    expand=True
                ), flush=True)

            self._output_buffer.clear()

        if self.error:
            for m in  self._error_buffer:
                panel_text = Text(m, style=Style(color="red"))
                rprint(Panel(
                    panel_text,
                    title=f"Server Output [red bold]{self.shell_prompt}[/red bold]",
                    title_align="left",
                    border_style="bold blue",
                    padding=(0, 1),
                    expand=True
                ), flush=True)

            self._error_buffer.clear()

        # Build the prompt + input line
        prompt = Text()
        prompt.append(f"{self.shell_prompt}", style="bold red")
        prompt.append(''.join(self._input_buffer), style="white")

        # Print the prompt line cleanly
        rprint(prompt, end='', flush=True)

    def exit(self):
        """
        Stop the console input loop and clear all buffers.
        Useful for gracefully shutting down the interface.
        """
        self.run = False
        self.clear()

    def clear(self):
        self._output_buffer.clear()
        self._input_buffer.clear()
        self.shell_prompt = '@remote-shell > '