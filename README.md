# Omasync new-device setup

This public launcher installs GitHub CLI through Omarchy's `mise`, opens GitHub browser authorization, and downloads the owner's **private** Omarchy profile to start its reviewed, resumable restore. No settings, secrets, or tokens live in this repository or its command.

On a fresh Omarchy laptop, paste one command:

```bash
curl -fsSL https://raw.githubusercontent.com/Countless9515/omasync-setup/main/setup.sh -o ~/omasync-setup.sh && bash ~/omasync-setup.sh
```

Review [`setup.sh`](setup.sh) before running remote code if you prefer. GitHub authorization and an explicit restore review still require your input; the optional `keyd` setup may ask for sudo. AUR packages may execute third-party build scripts if you select **all**; choose individual review to avoid blanket installation.

If the setup stops, run the same command again. It updates the cached clone with a fast-forward and resumes the private installer's completed phases. Your profile remains private and separate at [`Countless9515/omarchy-profile`](https://github.com/Countless9515/omarchy-profile).

Run tests with `python3 -B -m unittest discover -s tests -v`.
