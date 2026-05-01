#!/usr/bin/env node
/**
 * Install script for interactive-firmware-dev skill
 * 
 * This script is run when the skill is installed via npx skills add
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔧 Installing Interactive Firmware Development Skill...\n');

// Get the installation directory
const installDir = __dirname;

// Make scripts executable
try {
  console.log('Making scripts executable...');
  execSync('chmod +x scripts/*.py scripts/*.sh', { cwd: installDir, stdio: 'inherit' });
  console.log('✓ Scripts are now executable\n');
} catch (error) {
  console.error('⚠️  Warning: Could not make scripts executable automatically');
  console.log('   Run: chmod +x scripts/*.py scripts/*.sh\n');
}

// Check for required dependencies
console.log('Checking dependencies...');

// Check for Python 3
try {
  execSync('python3 --version', { stdio: 'pipe' });
  console.log('✓ Python 3 is installed');
} catch (error) {
  console.error('✗ Python 3 is not installed. Please install it first.');
  process.exit(1);
}

// Check for Zenity
try {
  execSync('which zenity', { stdio: 'pipe' });
  console.log('✓ Zenity is installed');
} catch (error) {
  console.error('✗ Zenity is not installed.');
  console.log('   Install with: sudo apt-get install zenity  (Debian/Ubuntu)');
  console.log('              or: sudo dnf install zenity      (Fedora)');
  console.log('              or: sudo pacman -S zenity        (Arch)\n');
}

console.log('\n📦 Installation complete!\n');
console.log('Usage:');
console.log('  npx interactive-firmware-dev --project ./my_project --port /dev/ttyUSB0');
console.log('  ./scripts/interactive_session.py --project ./my_project\n');
console.log('For more information, see README.md');
