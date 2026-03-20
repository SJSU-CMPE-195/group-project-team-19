### 1. First-Time Setup
```bash
git clone https://github.com/SJSU-CMPE-195/group-project-team-19.git
cd group-project-team-19 

=======
git config user.name "Your Name"
git config user.email "you@example.com"
```

### 2. Keeping Main Updated
```bash
git checkout main
git pull origin main
```

### 3. Fetching All Remote Branches
```bash
# Get all remote branches and tags
git fetch --all

# See all branches (local and remote)
git branch -a
```

### 4. Creating Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b feature/<short-description>
```

### 5. Making Changes and Committing
```bash
# Stage your changes
git add <file1> <file2>

# Commit with a descriptive message
git commit -m "Add servo PWM frequency control

- Implement configurable PWM frequency range
- Add boundary checking for pulse widths
- Include comprehensive inline documentation"
```

### 6. Pushing Your Branch
```bash
# First time pushing this branch
git push -u origin feature/<short-description>

# Subsequent pushes
git push
```








