# bob_sessions

Exported IBM Bob IDE task session reports. Required deliverable for the IBM Bob Hackathon.

Each subfolder belongs to one team member. Inside each member folder, every project-related Bob task gets its own subfolder containing:

- `summary.png`: screenshot of the Bob task session consumption summary panel.
- `history.md`: markdown file exported from Bob's History panel via the **Export task history** icon.

## Export procedure (from the hackathon guide, page 18-19)

1. In the Bob IDE chat interface, click **Views and More Actions** (the `...` icon next to the title bar) and select **History**.
2. Confirm you are in the correct project workspace at the top of the History panel. If your submission spans multiple workspaces, select **All**.
3. From the task history list, click the task related to this project. The task opens in the chat panel.
4. Click the **task header**. A task session consumption summary panel appears with Context Length, Task Id, Tokens, Cache, API Cost, and Size.
5. **Take a screenshot** of the consumption summary panel. Save it as `summary.png` in the appropriate subfolder.
6. In the same summary panel, click the **Export task history** icon (download arrow at the bottom left). A markdown file downloads.
7. Move the markdown into the same subfolder as `history.md`.
8. Commit both files to the repo. They are part of the submission.

## Folder convention

```
bob_sessions/
├── README.md
├── neel/
│   └── p0.1-foundation/
│       ├── summary.png
│       └── history.md
├── ben/
├── jacob/
└── alexie/
```

Task subfolder naming: `<priority-id>-<short-slug>` (e.g. `p0.1-foundation`, `p1.2-mcp-server`).

## Important notes

- This folder is part of the public repo. **Scrub each exported markdown before committing.** Remove anything that names other AI tools, API keys, IBM Cloud credentials, Bob credentials, or internal team workflow notes. IBM Security will deactivate your account if Bob or Cloud credentials are detected in a public repo.
- Use the **hackathon-provisioned Bob account** (`ibm-coding-challenge-xxx`) for every task. Personal Bob accounts will not be evidenced as hackathon work.
- One Bob task per feature (not per file). Multiple turns inside one task share context, which is cheaper on Bobcoins.
