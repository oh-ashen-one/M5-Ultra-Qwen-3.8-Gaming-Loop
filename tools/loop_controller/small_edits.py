"""Exact read-backed small replacements; model authors only a selected span."""
from .core import sha


class SelectedEdit:
    def __init__(self, files, path, start, end, max_lines=40):
        self.files,self.path,self.max_lines=files,path,max_lines
        raw=files.path(path).read_bytes()
        lines=raw.decode().splitlines(keepends=True)
        if not 1<=start<=end<=len(lines):raise ValueError('Invalid selected line range')
        self.before=sha(raw)
        self.old=''.join(lines[start-1:end])
        if raw.decode().count(self.old)!=1:raise ValueError('Selected span is not unique')
        self.start,self.end=start,end

    def apply(self, action, content):
        if not isinstance(content,str) or len(content.encode())>6000 or len(content.splitlines())>self.max_lines:
            raise ValueError('Keep the replacement within the selected small-edit budget')
        if self.old.endswith('\n') and not content.endswith('\n'):content+='\n'
        return self.files.edit(action,self.path,self.before,old=self.old,new=content)
