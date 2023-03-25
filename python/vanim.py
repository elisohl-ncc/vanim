import vim  # type: ignore
import os.path
import ast
from os import scandir, stat


MANIM_VERSION_SUFFIX = "_v0.17.2"  # TODO FIXME this should not be hardcoded lol


class VanimError(Exception): pass


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
        nodes = list(self._get_scene_nodes())
        # look for a scene under the cursor
        for node in nodes:
            if node.lineno <= cur_line <= node.end_lineno:
                return node.name
        raise VanimError("no scene under cursor")

    @staticmethod
    def _get_scene_nodes():
        source = "\n".join(vim.current.buffer)  # pack entire buffer into a string lol
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
        candidates = self._get_videos() + self._get_image()
        most_recent = max(candidates, key=lambda path: stat(path).st_mtime)
        viewer = "vlc " if most_recent.endswith(".mp4") else "eog "
        gnome_command = self.wrap_in_gnome_terminal(viewer + most_recent)
        vim_command = f"execute 'silent !{gnome_command}' | redraw!"
        vim.command(vim_command)
        return [stat(path).st_mtime for path in candidates]

    def _get_videos(self):
        file_dir = os.path.join("media", "videos", self.file[:-3])
        file_subdirs = [dirent.name for dirent in scandir(file_dir)]
        return tuple(
            file for subdir in file_subdirs
            if os.path.isfile(file := os.path.join(file_dir, subdir, self.scene + ".mp4"))
        )

    def _get_image(self):
        file = os.path.join("media", "images", self.file[:-3], self.scene + MANIM_VERSION_SUFFIX + ".png")
        with open("/tmp/foo", "w") as f: f.write(str(file))
        if os.path.isfile(file):
            return (file,)
        return ()
