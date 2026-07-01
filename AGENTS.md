# Instructions for AI Agents Updating Presentation Slides

When modifying or updating the presentation slides in this repository, you must follow this sequential workflow:

1. **Update the Markdown Slides First:**
   Always modify the Marp-compatible markdown file [presentation/slides.md](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/presentation/slides.md) first. Update the outline, slide contents, text structure, and speaker metadata here.

2. **Synchronize the LaTeX Beamer Document:**
   Replicate the modifications into the LaTeX Beamer file [presentation/slides.tex](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/presentation/slides.tex) to ensure both file types stay perfectly in sync.

3. **Recompile the Slide Deck:**
   Run the compilation build command from the terminal in the root directory:
   ```bash
   make
   ```
   This will execute the `pdflatex` build process on `slides.tex` and regenerate the compiled PDF document [presentation/slides.pdf](file:///Users/huutrungle2001/Documents/OnGoing/NVIDIA_cuOpt/presentation/slides.pdf).

4. **Verify and Push Changes:**
   Commit the source changes and the rebuilt PDF, then push to the remote repository. Do not track intermediate build outputs (such as `.aux`, `.log`, `.nav`, etc.) which are ignored via `.gitignore`.
