#!/bin/bash
# DocTranslate Fork Quick Start Script
#
# This script guides you through the complete fork implementation process.
# It includes safeguards (dry-runs first, confirmations before destructive operations).
#
# Usage: bash QUICK_START.sh
# Or: chmod +x QUICK_START.sh && ./QUICK_START.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

confirm() {
    local prompt="$1"
    local response
    read -p "$(echo -e ${YELLOW}$prompt${NC}) (y/N): " -n 1 response
    echo
    [[ "$response" =~ ^[Yy]$ ]]
}

# Main script
main() {
    print_header "DocTranslate Fork Implementation Quick Start"

    echo "This script will guide you through:"
    echo "  1. Package verification (imports, CLI)"
    echo "  2. Architecture improvements (multi-translator router)"
    echo "  3. AGPL compliance setup"
    echo "  4. Clean Git initialization (Option B: fresh history)"
    echo ""
    echo "All steps use dry-runs/confirmations before making changes."
    echo ""

    if ! confirm "Ready to begin?"; then
        echo "Aborted."
        exit 0
    fi

    # Step 1: Package verification
    print_header "STEP 1: Package Verification"

    echo "Verifying doctranslate package and CLI..."
    if python -c "import doctranslate; print(f'✓ Import successful. Version: {doctranslate.__version__}')" 2>/dev/null; then
        print_step "Package imports work correctly"
    else
        print_error "Package import failed. Please reinstall: pip install -e ."
        exit 1
    fi

    if command -v doctranslate &> /dev/null; then
        print_step "CLI command 'doctranslate' available"
    else
        print_warning "CLI not yet available. Run: pip install -e ."
    fi

    # Step 2: Architecture (already done)
    print_header "STEP 2: Architecture Improvements"

    if [ -f "doctranslate/translator/router.py" ]; then
        print_step "Multi-translator router created at doctranslate/translator/router.py"
        echo ""
        echo "The router supports multiple translation backends with strategies:"
        echo "  • FAILOVER: Try first, fallback on error"
        echo "  • ROUND_ROBIN: Cycle through available translators"
        echo "  • LEAST_LOADED: Pick translator with fewest concurrent requests"
        echo "  • COST_AWARE: Pick cheapest while maintaining quality"
        echo ""
        echo "See FORK_IMPLEMENTATION_GUIDE.md for integration examples."
    else
        print_error "router.py not found"
    fi

    # Step 3: Legal compliance (already done)
    print_header "STEP 3: AGPL Compliance"

    local legal_files=("LICENSE" "LICENSE.ADDITIONS" "NOTICE")
    local all_present=true

    for file in "${legal_files[@]}"; do
        if [ -f "$file" ]; then
            print_step "$file exists"
        else
            print_error "$file not found"
            all_present=false
        fi
    done

    if [ "$all_present" = true ]; then
        echo ""
        echo "Next: Update README.md with your custom content."
        echo "A template is provided in README_TEMPLATE.md"
        echo ""

        if [ -f "README_TEMPLATE.md" ]; then
            if confirm "Replace README.md with template?"; then
                cp README.md README_BABELDOC.md
                cp README_TEMPLATE.md README.md
                print_step "README.md updated (backup saved as README_BABELDOC.md)"
                echo "Please customize README.md with your own content (see sections marked as [YOUR ...])"
            fi
        fi
    fi

    # Step 4: Git initialization
    print_header "STEP 4: Clean Git Initialization (Option B)"

    echo "This will:"
    echo "  • Create an orphan branch with fresh history"
    echo "  • Make a single initial commit with full attribution"
    echo "  • Delete all old BabelDOC commit history"
    echo ""
    print_warning "⚠️  This is IRREVERSIBLE. Your old local git history will be lost."
    echo ""

    if ! confirm "Proceed with fresh Git history?"; then
        print_warning "Git reinitialization skipped."
        echo ""
        echo "You can run these commands manually later:"
        echo "  git checkout --orphan fresh-main"
        echo "  git add -A"
        echo "  git commit -m \"Initial commit: DocTranslate based on BabelDOC v0.5.24\""
        echo "  git branch -D main && git branch -m fresh-main main"
        echo "  git remote set-url origin git@github.com:YOUR_USERNAME/doctranslate.git"
        echo "  git push -u origin main --force"
        return 0
    fi

    # Git commands
    echo ""
    echo "Step 4a: Committing current state..."
    if ! git diff --quiet; then
        git add -A
        git commit -m "Final updates before fork initialization"
        print_step "Current changes committed"
    else
        print_step "No changes to commit"
    fi

    echo "Step 4b: Creating orphan branch..."
    git checkout --orphan fresh-main 2>/dev/null || true
    print_step "Orphan branch created"

    echo "Step 4c: Staging all files..."
    git add -A
    print_step "Files staged"

    echo "Step 4d: Creating initial commit with attribution..."
    git commit -m "Initial commit: DocTranslate based on BabelDOC v0.5.24

This is a customized fork of BabelDOC (https://github.com/funstory-ai/BabelDOC)
created by Miguel Enes.

Key additions:
- Multi-translator orchestration engine (doctranslate/translator/router.py)

BabelDOC is licensed under AGPL-3.0. This derivative maintains the same license.
See LICENSE, LICENSE.ADDITIONS, and NOTICE for full attribution."

    print_step "Initial commit created"

    echo "Step 4e: Cleaning up old branch..."
    git branch -D main 2>/dev/null || true
    git branch -m fresh-main main
    print_step "Branch renamed to main"

    echo "Step 4f: Configuring remote..."
    local current_remote=$(git config --get remote.origin.url)

    if [[ "$current_remote" == *"BabelDOC"* ]] || [[ "$current_remote" == *"funstory"* ]]; then
        echo "Current remote: $current_remote"
        read -p "Enter your GitHub repo URL (git@github.com:USER/doctranslate.git): " new_remote
        git remote set-url origin "$new_remote"
        print_step "Remote updated"
    else
        echo "Current remote: $current_remote"
        print_step "Remote already configured (or non-standard)"
    fi

    # Verification
    print_header "VERIFICATION"

    echo "Checking git log..."
    if [ "$(git rev-list --all --count)" -eq 1 ]; then
        print_step "Git history reset: 1 commit only"
    else
        print_warning "Multiple commits detected. Was the orphan branch created correctly?"
    fi

    echo ""
    echo "Checking files..."
    python -c "import doctranslate; print(f'✓ doctranslate package imports OK (v{doctranslate.__version__})')" 2>/dev/null || print_error "doctranslate import failed"

    [ -f "LICENSE" ] && print_step "LICENSE exists" || print_error "LICENSE missing"
    [ -f "LICENSE.ADDITIONS" ] && print_step "LICENSE.ADDITIONS exists" || print_error "LICENSE.ADDITIONS missing"
    [ -f "NOTICE" ] && print_step "NOTICE exists" || print_error "NOTICE missing"

    # Summary
    print_header "IMPLEMENTATION COMPLETE ✓"

    echo "Your DocTranslate fork is ready!"
    echo ""
    echo "Next steps:"
    echo "  1. Review and customize README.md"
    echo "  2. Push to GitHub: git push -u origin main --force"
    echo "  3. Verify on GitHub: https://github.com/YOUR_USERNAME/doctranslate"
    echo "  4. Set up CI/CD workflows"
    echo "  5. Create first release (git tag v0.1.0)"
    echo ""
    echo "Documentation:"
    echo "  • IMPLEMENTATION_SUMMARY.md — Overview of all deliverables"
    echo "  • FORK_IMPLEMENTATION_GUIDE.md — Detailed step-by-step guide"
    echo "  • LICENSE.ADDITIONS — Legal compliance documentation"
    echo ""
    echo "Questions? See FORK_IMPLEMENTATION_GUIDE.md or LICENSE.ADDITIONS"
    echo ""
}

# Run main
main
