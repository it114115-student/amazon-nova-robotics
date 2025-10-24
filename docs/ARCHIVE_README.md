# Archived documentation

Files moved here were considered non-essential or outdated by the cleanup script.
They are preserved in their original relative paths under this folder.

- To restore a file, move it back to its original location.
- To adjust what gets archived, edit `docs/cleanup_config.json` and re-run the cleanup.

Run dry-run preview first:

```bash
python3 docs/cleanup_rubbish.py --dry-run
```

Archive candidates instead of deleting:

```bash
python3 docs/cleanup_rubbish.py --archive --yes
```

Permanently delete candidates (irreversible):

```bash
python3 docs/cleanup_rubbish.py --delete --yes
```
