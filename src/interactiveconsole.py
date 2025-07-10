from blessed import Terminal
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
import pyfiglet
import readline

BOLD = "\033[1m"
GREEN = "\033[32m"
RESET = "\033[0m"
RED = "\033[31m"


class InteractiveConsole:
    """
    A terminal-based interactive shell for a reverse shell server interface.
    Provides input handling, output rendering, and a styled interface using 'blessed' and 'rich'.
    """

    def __init__(self, logo='', shell=''):
        """
        Initialize the interactive console.

        :param logo: Optional ASCII logo to display using pyfiglet.
        :param shell: Custom shell prompt string.
        """
        if logo:
            print('\n' + f'{GREEN}{BOLD}' + pyfiglet.figlet_format("rever\n sync".upper(),
                                                                   font="amc_aaa01") + f'{logo}' + f'{RESET}' + '\n')
        self._term = Terminal()
        self._error_buffer = []  # Stores error messages to be rendered
        self._output_buffer = []  # Stores standard output messages to be rendered
        self._input_buffer = []  # Current user input characters as a list
        self.shell_prompt = shell  # Prompt label displayed before user input
        self.run = True  # Main input loop controller
        self._history_index = 1  # Tracks current position in history
        self._cursor_position = len(self._input_buffer)  # Current position in the input buffer

    def log(self,message):
        Console().log(message,justify='center')

    def line(self,message=''):
        Console().rule(message)

    @property
    def output(self):
        """Get the current output buffer."""
        return self._output_buffer

    @output.setter
    def output(self, message):
        """
        Append a message to the output buffer and display it.

        :param message: Text to be added to output.
        """
        self._output_buffer.append(message)
        self.print()

    @property
    def error(self):
        """Get the current error buffer."""
        return self._error_buffer

    @error.setter
    def error(self, message):
        """
        Append an error message to the error buffer and display it.

        :param message: Error message string.
        """
        self._error_buffer.append(message)
        self.print()

    def _move_left(self):
        """Move the cursor one position to the left within the input buffer."""
        if self._cursor_position > 0:
            y, x = self._term.get_location(0.1)
            self._cursor_position = max(0, self._cursor_position - 1)
            if self._input_buffer[self._cursor_position] == '\n':
                self._clear_prompt()
                self._get_prompt()
                print(''.join(self._input_buffer[:self._cursor_position]), end='', flush=True)
                with self._term.location():
                    print(''.join(self._input_buffer[self._cursor_position:]), end='', flush=True)
            else:
                if x == 0:
                    print(self._term.move_up + self._term.move_x(self._term.width), end='', flush=True)
                else:
                    print(self._term.move_left, end='', flush=True)

    def _move_right(self):
        """Move the cursor one position to the right within the input buffer."""
        if self._cursor_position < len(self._input_buffer):
            y, x = self._term.get_location(0.1)
            if x == self._term.width - 1 or self._input_buffer[self._cursor_position] == '\n':
                print(self._term.move_down + self._term.move_x(0), end='', flush=True)
            else:
                print(self._term.move_right, end='', flush=True)
            self._cursor_position = min(len(self._input_buffer), self._cursor_position + 1)

    def _navigate_up(self):
        # Navigate up in history
        prev = readline.get_history_item(self._history_index)
        if prev:
            self._clear_prompt()
            self._input_buffer = list(prev)
            self._cursor_position = len(self._input_buffer)
            self._history_index = max(1, self._history_index - 1)
            self._get_prompt()
            print(''.join(self._input_buffer), end='', flush=True)

    def _navigate_down(self):
        # Navigate down in history
        next_item = readline.get_history_item(self._history_index)
        if next_item:
            self._clear_prompt()
            self._input_buffer = list(next_item)
            self._cursor_position = len(self._input_buffer)
            self._history_index = min(self._history_index + 1, readline.get_current_history_length())
            self._get_prompt()
            print(''.join(self._input_buffer), end='', flush=True)
        else:
            self._input_buffer.clear()

    def _delete(self):
        """
        Delete a character to the left of the cursor and update the display.
        """
        if self._input_buffer and not self._cursor_position == 0:
            self._cursor_position = max(0, self._cursor_position - 1)
            self._clear_prompt()
            self._get_prompt()
            self._input_buffer.pop(self._cursor_position)
            print(''.join(self._input_buffer[:self._cursor_position]), end='', flush=True)
            with self._term.location():
                print(''.join(self._input_buffer[self._cursor_position:]), end='', flush=True)

    def _go_to_end(self):
        self._clear_prompt()
        self._cursor_position = len(self._input_buffer)
        self._get_prompt()
        print(''.join(self._input_buffer), end='', flush=True)

    def _go_to_beginning(self):
        self._clear_prompt()
        self._cursor_position = 0
        self._get_prompt()
        with self._term.location():
            print(''.join(self._input_buffer), end='', flush=True)

    def _new_line(self):
        self._print_key('\n')

    def _get_prompt(self):
        prompt = Text()
        prompt.append(self.shell_prompt, style="bold red")
        rprint(prompt, end='', flush=True)

    def input(self):
        """
        Handle interactive user input loop.
        :return: The final command string entered by the user.
        """
        self.print()
        with self._term.cbreak():
            while self.run:
                key = self._term.inkey(0.1)
                if not key:
                    continue
                match key.name:
                    case 'KEY_UP':
                        self._navigate_up()
                    case 'KEY_DOWN':
                        self._navigate_down()
                    case 'KEY_LEFT':
                        self._move_left()
                    case 'KEY_RIGHT':
                        self._move_right()
                    case 'KEY_BACKSPACE':
                        self._delete()
                    case 'KEY_ENTER':
                        # Process entered command
                        data = ''.join(self._input_buffer).strip()
                        if not data:
                            continue
                        self.print_input(data)
                        for i in range(1, readline.get_current_history_length() + 1):
                            if data.strip() == readline.get_history_item(i).strip():
                                return data
                        readline.add_history(data)
                        self._history_index = readline.get_current_history_length()
                        return data

                match key.encode():
                    case b'\x05':  # ctrl+E go to the end of line
                        self._go_to_end()
                    case b'\x01':  # ctrl+A go to the beginning of line
                        self._go_to_beginning()
                    case b'\x0e':  # new line
                        self._new_line()
                if key.isprintable():
                    self._print_key(key)
            return ''

    def _print_key(self, key):
        """
        Print a single character input and update the buffer state and display.
        :param key: Single-character string to insert at cursor position.
        """
        if self._cursor_position == len(self._input_buffer):
            print(key, end='', flush=True)
            self._input_buffer.append(key)
            self._cursor_position = len(self._input_buffer)
        else:
            self._input_buffer.insert(self._cursor_position, key)
            y, x = self._term.get_location(0.1)
            if y == self._term.height - 1:
                with self._term.location():
                    print('\n', end='', flush=True)
                print(self._term.move_up(1), end='', flush=True)
            if x == self._term.width - 1:
                print('' + self._term.move_down(1) + self._term.move_x(0), end='', flush=True)
            print(self._term.clear_eos + key, end='', flush=True)
            with self._term.location():
                print(''.join(self._input_buffer[self._cursor_position + 1:]), end='', flush=True)
            self._cursor_position = min(len(self._input_buffer), self._cursor_position + 1)

    def print_input(self, data: str):
        """
        Print the most recent command entered by the user inside a rich panel.
        :param data: The string command to display.
        """
        self._history_index = 1
        prompt = Text(data, style="white")
        if self._cursor_position < len(self._input_buffer) and self._input_buffer[self._cursor_position] == '\n':
            print()
        self._clear_prompt()
        rprint(Panel(
            prompt,
            title=f"[bold green]Input[/bold green] [red]{self.shell_prompt}[/red]",
            title_align='left',
            border_style="bold green",
            padding=(0, 1),
            expand=True,
            box=box.ASCII2
        ), flush=True)
        self._input_buffer.clear()
        self._cursor_position = self._cursor_position = len(self._input_buffer)

    def print(self):
        """
        Render all buffered messages (output + error) in styled panels.
        Re-renders the current shell prompt and partially typed input.
        """
        if self.shell_prompt or self._input_buffer:
            self._clear_prompt()
        if self.output:
            for msg in self._output_buffer:
                rprint(Panel(
                    Text(msg, style="white"),
                    title=f"Output [green]{self.shell_prompt}[/green]",
                    title_align="left",
                    border_style="bold blue",
                    padding=(0, 1),
                    expand=True
                ), flush=True)
            self._output_buffer.clear()

        if self.error:
            for msg in self._error_buffer:
                rprint(Panel(
                    Text(msg, style="red"),
                    title=f"[red]Error[/red] [green]{self.shell_prompt}[/green]",
                    title_align="left",
                    border_style="bold red",
                    padding=(0, 1),
                    expand=True
                ), flush=True)
            self._error_buffer.clear()

        if self.shell_prompt or self._input_buffer:
            prompt = Text()
            prompt.append(f"{self.shell_prompt}", style="bold red")
            prompt.append(''.join(self._input_buffer), style="white")
            rprint(prompt, end='', flush=True)
            self._cursor_position = self._cursor_position = len(self._input_buffer)

    def exit(self):
        """
        Terminate the input loop and reset the console state.
        Useful for graceful shutdown.
        """
        self.run = False
        self.clear()
        self._clear_prompt()

    def clear(self):
        """
        Clear all buffers and reset prompt state.
        """
        self._output_buffer.clear()
        self._input_buffer.clear()
        self.shell_prompt = '@remote-shell > '

    def _get_cursor_terminal_line(self) -> int:
        """
        Calculates which visual terminal line (0-based index) the cursor is on,
        accounting for line wrapping, newlines, and the shell prompt.

        Returns:
            int: The index (1-based) of the terminal line where the cursor is currently positioned.
        """
        full_input = self.shell_prompt + ''.join(self._input_buffer)

        # Map each character to its original index for position tracking
        char_indices = list(range(len(full_input)))

        # Split on newlines
        logical_lines = full_input.splitlines(keepends=True)

        # wrap each logical line to the terminal width
        wrapped_lines = []  # Contains wrapped text lines
        wrapped_indices = []  # Tracks original character indices per line
        current_index = 0  # Tracks position in char_indices

        for line in logical_lines:
            if len(line) > self._term.width:
                # Wrap long lines manually using terminal width
                for segment in self._term.wrap(line, width=self._term.width):
                    wrapped_lines.append(segment)
                    wrapped_indices.append(char_indices[current_index: current_index + len(segment)])
                    current_index += len(segment)

                # Preserve the newline visually if it existed
                if line.endswith('\n'):
                    wrapped_lines[-1] += '\n'
                    wrapped_indices[-1].append(char_indices[current_index])  # Include the newline index
                    current_index += 1
            else:
                wrapped_lines.append(line)
                wrapped_indices.append(char_indices[current_index: current_index + len(line)])
                current_index += len(line)

        # Determine which wrapped line the cursor is currently on
        cursor_line_index = len(wrapped_lines)
        absolute_cursor_pos = len(self.shell_prompt) + self._cursor_position

        for i, line_indices in enumerate(wrapped_indices, start=1):
            if absolute_cursor_pos in line_indices:
                cursor_line_index = i
                break

        return cursor_line_index

    def _clear_prompt(self):
        """
        Clear the prompt line including wrapped lines in the terminal.
        """
        position = self._get_cursor_terminal_line()
        print(self._term.move_x(0), end='', flush=True)
        if self._cursor_position < len(self._input_buffer) and self._input_buffer[self._cursor_position] == '\n':
            print(self._term.move_up, end='', flush=True)
        if position > 1:
            print(self._term.move_up(position - 1), end='', flush=True)
        print(self._term.clear_eos, end='', flush=True)
