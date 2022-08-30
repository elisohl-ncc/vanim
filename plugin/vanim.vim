" quit if vanim is disabled
if exists('g:vanim_plugin_disable')
    finish
endif

" quit if vanim has already been loaded
if exists('g:vanim_plugin_loaded')
    finish
endif

" quit if python3 is not available
if !has("python3")
    echo "vanim requires vim to be compiled with python3 support"
    finish
endif

" get plugin's root dir
let s:vanim_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

" add plugin's root dir to pythonpath, and import and run main class
python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:vanim_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
from vanim import Vanim
vanim = Vanim()
EOF

" command bindings
command! -nargs=? VanimRenderL :python3 vanim.render("l", <args>)
command! -nargs=? VanimRenderM :python3 vanim.render("m", <args>)
command! -nargs=? VanimRenderH :python3 vanim.render("h", <args>)
command! -nargs=? VanimRenderP :python3 vanim.render("p", <args>)
command! -nargs=? VanimRenderK :python3 vanim.render("k", <args>)
command! -nargs=? VanimRenderAll :python3 vanim.render_all(<args>)

" set a flag to indicate that this file has been run
let g:vanim_plugin_loaded = 1

