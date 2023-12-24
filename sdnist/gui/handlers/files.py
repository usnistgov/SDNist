from typing import Dict, Optional
from pathlib import Path
import re
import pandas as pd
import shutil

from sdnist.gui.strs import *
from sdnist.gui.constants import (
    ARCHIVE_DIR_PREFIX, REPORT_DIR_PREFIX,
    METAREPORT_DIR_PREFIX)

from sdnist.report.dataset.target import TargetLoader

CHILD = 'Child '
counts_list = [REPORTS, METAREPORTS, ARCHIVE_FILES, INDEX_FILES, DEID_CSV_FILES, META_DATA_FILES]
child_counts_list = [CHILD + k for k in counts_list]

# Combine them into a single regex pattern
non_deid_dir_pattern = '|'.join([re.escape(REPORT_DIR_PREFIX),
                    re.escape(ARCHIVE_DIR_PREFIX),
                    re.escape(METAREPORT_DIR_PREFIX),
                    re.escape(REPORTS.lower()),
                    re.escape(METAREPORTS.lower()),
                    re.escape(ARCHIVES.lower())])
class DirectoryNode:
    def __init__(self,
                 path: Path,
                 parent: Optional["DirectoryNode"] = None):
        self.path = path
        self.parent = parent
        self.counts = {
            DEID_CSV_FILES: 0,
            META_DATA_FILES: 0,
            REPORTS: 0,
            METAREPORTS: 0,
            INDEX_FILES: 0,
            ARCHIVE_FILES: 0,
        }
        self.children: Dict[Path, "DirectoryNode"] = dict()
        self.counts = dict()

    def add_child(self, child_node: "DirectoryNode"):
        self.children[child_node.path] = child_node

    def set_counts(self, counts: Dict[str, int]):
        self.counts = counts

class FilesTreeHandler:
    def __init__(self, root: Path, target_loader: TargetLoader):
        self.root = root
        self.target_loader = target_loader
        self.nodes: Dict[Path, DirectoryNode] = dict()
        self.leafs: Dict[Path, DirectoryNode] = dict()
        self._create_tree()

    def _create_tree(self):

        root_node = DirectoryNode(
            path=self.root
        )
        root_node.set_counts(self.create_counts(self.root))

        def subtree(_root: Path, _root_node: DirectoryNode):
            n_children = 0
            self.nodes[_root] = _root_node
            for f in _root.iterdir():
                if f.is_file():
                    pass
                elif f.is_dir():
                    # Check if any of the constant strings match in f.name
                    is_deid_dir = not re.search(non_deid_dir_pattern, f.name)
                    if is_deid_dir:
                        counts = self.create_counts(f)
                        child_node = DirectoryNode(
                            path=f,
                            parent=_root_node
                        )
                        child_node.set_counts(counts)
                        _root_node.add_child(child_node)
                        subtree(f, child_node)
                        n_children += 1
            if n_children == 0:
                self.leafs[_root] = _root_node

        subtree(self.root, root_node)
        self.add_counts_to_parents()

    def add_counts_to_parents(self):
        leafs = list(self.leafs.keys())
        while len(leafs) > 0:
            new_leafs = set()
            for l_path in leafs:
                l_node = self.nodes[l_path]
                parent = l_node.parent
                if parent:
                    for k in counts_list:
                        parent.counts[k] += l_node.counts[k]
                    new_leafs.add(parent.path)
            leafs = list(new_leafs)

    def create_counts(self, dir_path: Path):
        counts = {
            DEID_CSV_FILES: 0,
            META_DATA_FILES: 0,
            REPORTS: 0,
            METAREPORTS: 0,
            INDEX_FILES: 0,
            ARCHIVE_FILES: 0,
        }
        child_counts = {CHILD + k: 0 for k, _ in counts.items()}
        counts = {**counts, **child_counts}

        if dir_path.is_file():
            return counts

        for path in dir_path.iterdir():
            if path.is_file():
                if path.suffix == '.csv' and 'index' not in path.name:
                    df = pd.read_csv(path, nrows=0)
                    is_deid_csv = self.target_loader.is_deid_csv(df)
                    del df
                    if is_deid_csv:
                        counts[CHILD + DEID_CSV_FILES] += 1
                elif path.suffix == '.json':
                    d_csv = Path(str(path).replace('.json', '.csv'))
                    if d_csv.exists():
                        counts[CHILD + META_DATA_FILES] += 1
                elif path.suffix == '.csv' and 'index' in path.name:
                    counts[CHILD + INDEX_FILES] += 1
            elif path.is_dir():
                if REPORTS.lower() in path.name:
                    for rep_path in path.iterdir():
                        if (rep_path.is_dir()
                            and REPORT_DIR_PREFIX in rep_path.name):
                            report_json = Path(rep_path, 'report.json')
                            report_html = Path(rep_path, 'report.html')
                            if report_html.exists() and report_json.exists():
                                counts[CHILD + REPORTS] += 1
                            else:
                                shutil.rmtree(rep_path)
                elif METAREPORTS.lower() in path.name:
                    for metareport_path in path.iterdir():
                        if (metareport_path.is_dir()
                            and METAREPORT_DIR_PREFIX in metareport_path.name):
                            metareport_json = Path(metareport_path, 'report.json')
                            ui_json = Path(path, 'ui.json')
                            if metareport_json.exists() and ui_json.exists():
                                counts[CHILD + METAREPORTS] += 1
                            else:
                                shutil.rmtree(metareport_path)
                elif ARCHIVES.lower() in path.name:
                    for archive_path in path.iterdir():
                        if (archive_path.is_dir()
                            and ARCHIVE_DIR_PREFIX in archive_path.name):
                            index_path = Path(archive_path, 'index.csv')
                            if index_path.exists():
                                counts[CHILD + ARCHIVE_FILES] += 1
                            else:
                                shutil.rmtree(archive_path)
        for k in counts_list:
            counts[k] = counts[CHILD + k]
        return counts

    def get_counts(self, path: Path):
        if path in self.nodes:
            return {k: self.nodes[path].counts[k]
                    for k in counts_list}
        else:
            return {k: 0 for k in counts_list}

    def update_count(self, path: Path):
        deid_leaf = path.parent
        while deid_leaf and deid_leaf not in self.nodes:
            deid_leaf = deid_leaf.parent

        new_counts = self.create_counts(deid_leaf)
        leaf_counts = self.nodes[deid_leaf].counts
        change_count = 0
        change_file_key = None
        total_keys = []
        for k, ck in zip(counts_list, child_counts_list):
            diff = new_counts[ck] - leaf_counts[ck]
            if diff:
                change_count = diff
                total_keys.append((ck, change_count))
                change_file_key = k

        if change_count:
            node = self.nodes[deid_leaf]
            node.counts[CHILD + change_file_key] += change_count
            while node:
                node.counts[change_file_key] += change_count
                node = node.parent
