# Assets for SemShift

This directory contains visual assets used in the main README and documentation.

## Adding Demo Materials

### Demo GIF

To showcase SemShift in action:

1. **Record a demo**: Capture terminal output showing `semshift compare` command with rich formatting
   ```bash
   # Example command to record
   semshift compare examples/old_policy.md examples/new_policy.md --mode policy
   ```

2. **Save the GIF**: 
   - Use a tool like [asciinema](https://asciinema.org/) or [terminalizer](https://www.terminalizer.com/)
   - Export as `.gif` format
   - Place in this `assets/` directory as `demo.gif`

3. **Update the main README**:
   ```markdown
   ![SemShift Demo](assets/demo.gif)
   ```

### Screenshots

For UI/output examples:

1. **Capture**: Screenshot or screen recording of SemShift output
2. **Save**: Place in this directory with descriptive filename
   - `policy-example.png` - Example policy drift detection
   - `github-action-example.png` - GitHub Action in PR
   - `cli-output-example.png` - Terminal output example
3. **Optimize**: Compress to keep file size < 5MB
4. **Reference**: Link from README with alt text:
   ```markdown
   ![Policy drift example output](assets/policy-example.png)
   ```

## Asset Guidelines

- **Format**: PNG for screenshots, GIF for animations
- **Size**: Keep files < 5MB for better web performance
- **Alt text**: Always include descriptive alt text in markdown
- **Naming**: Use descriptive, lowercase filenames with hyphens (e.g., `policy-drift-example.png`)
- **Accessibility**: Ensure good contrast and readability
- **Directory structure**: Keep all assets in this single directory for easy management

## Current Assets

*(Add entries as new assets are created)*

- `demo.gif` - Terminal demo of SemShift comparing policy files (placeholder)
