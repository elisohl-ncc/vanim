import vim  # type: ignore
import os.path
import ast
from os import scandir, stat


class Vanim:
    @property
    def cwd(self):
        return os.path.dirname(vim.current.buffer.name)

    @property
    def file(self):
        return os.path.basename(vim.current.buffer.name)

    @property
    def scene(self):
        cur_line, _ = vim.current.window.cursor
        for node in self._get_scene_nodes():
            if node.lineno <= cur_line <= node.end_lineno:
                return node.name
        return None  # NOTE should this be an error?

    @staticmethod
    def _get_scene_nodes():
        source = '\n'.join(vim.current.buffer)  # pack entire buffer into a string lol
        parsed = ast.parse(source)
        for node in ast.walk(parsed):
            if not isinstance(node, ast.ClassDef):
                continue
            # this next test is a bit of a hack but oh well
            if not any("Scene" in base.id for base in node.bases):  # type: ignore
                continue
            yield node

    def wrap_in_gnome_terminal(self, shell_command):
        return f"gnome-terminal --working-directory={self.cwd} -q -- {shell_command}"

    def render(self, quality, scene=None, preview=True):
        scene = scene or self.scene
        assert scene is not None
        manim_flags = f"{'p' if preview else ''}q{quality}"
        manim_command = f"manim -{manim_flags} --save_sections {self.file} {scene}"
        prompt_command = r"echo \"Press Enter to close this window.\"; read" if preview else ""
        shell_command = f'sh -c "{manim_command}; {prompt_command}"'
        gnome_command = self.wrap_in_gnome_terminal(shell_command)
        vim_command = f"execute 'silent !{gnome_command}' | redraw!"
        # phew! that's a lot of commands!
        vim.command(vim_command)

    def render_all(self, quality="h"):
        for node in self._get_scene_nodes():
            self.render(quality, node.name, False)

    def show(self):
        video_dir = os.path.join("media", "videos", self.file[:-3])
        video_subdirs = [dirent.name for dirent in scandir(video_dir)]
        most_recent = max(
            (video for subdir in video_subdirs if os.path.isfile(video := os.path.join(video_dir, subdir, self.scene + ".mp4"))),
            key=lambda path: stat(path).st_mtime
        )
        gnome_command = self.wrap_in_gnome_terminal("vlc " + most_recent)
        vim_command = f"execute 'silent !{gnome_command}' | redraw!"
        vim.command(vim_command)
