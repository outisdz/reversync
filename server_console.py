import pyfiglet
from blessed import Terminal
from rich import print as rprint
from rich.panel import Panel
from rich.style import Style
from rich.text import Text


BOLD = "\033[1m"
GREEN = "\033[32m"
RESET = "\033[0m"
RED = "\033[31m"

class ServerConsole:
    """
    A terminal-based interactive shell for a reverse shell server interface.
    Provides input handling, output rendering, and styled interface using 'blessed' and 'rich'.
    """
    def __init__(self,logo):
        """Initialize terminal, buffers, and default shell_prompt."""

        self._term = Terminal()
        print('\n'+f'{GREEN}{BOLD}' + pyfiglet.figlet_format("rever\n sync".upper(),font="ghost") + f'\n{logo}' + f'{RESET}')

        self._output_buffer = []                    # Stores printed messages
        self._input_buffer = []                     # Stores currently typed characters
        self._shell_prompt = '@remote-shell > '     # Default prompt label
        self.run = True                             # Controls the main input loop


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

    def b_input(self,shell: str):
        """
        Main user input loop. Reads characters with basic handling for backspace and enter.
        :param shell: The shell prompt to show (e.g., "192.168.0.1@reverse-shell > ")
        :return: The final string input when the user presses Enter
        """
        self._shell_prompt = shell
        with self._term.cbreak():

            while self.run:
                self.print()
                key = self._term.inkey(0.1)
                if not key:
                    continue
                if key.name == 'KEY_BACKSPACE':
                    if self._input_buffer:
                        self._input_buffer.pop()
                        self.print()
                    continue
                if key.name == "KEY_ENTER":
                    self.print()
                    data = ''.join(self._input_buffer)
                    self._input_buffer.clear()
                    return data
                self._input_buffer.append(key)
            return ''


    def print(self):
        """
        Render all buffered output messages in styled panels.
        Also reprints the current shell prompt and partially typed command.
        """
        if self.output:
            # Clear current line and render each output panel
            print(self._term.clear_bol + self._term.move_x(0), end='', flush=True)
            for m in  self._output_buffer:
                panel_text = Text(m, style=Style(color="white"))
                rprint(Panel(
                    panel_text,
                    title=f"Server Output [red bold]{self._shell_prompt}[/red bold]",
                    title_align="left",
                    border_style="bold blue",
                    padding=(0, 1),
                    expand=True
                ), flush=True)
            self._output_buffer.clear()

        # Build the prompt + input line
        prompt = Text()
        prompt.append(f"{self._shell_prompt}", style="bold red")
        prompt.append(''.join(self._input_buffer), style="white")

        # Print the prompt line cleanly
        print(
            self._term.clear_bol + self._term.move_x(0),
            end='', flush=True
        )
        rprint(prompt, end='', flush=True)

    def exit(self):
        """
        Stop the console input loop and clear all buffers.
        Useful for gracefully shutting down the interface.
        """
        self._output_buffer.clear()
        self._input_buffer.clear()
        self.run = False

    def clear(self):
        self._output_buffer.clear()
        self._input_buffer.clear()
        self._shell_prompt = '@remote-shell > '

