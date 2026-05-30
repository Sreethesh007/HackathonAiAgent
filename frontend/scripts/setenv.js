const fs = require('fs');
const path = require('path');

// Configure dotenv to load environment variables from a .env file into process.env
require('dotenv').config();

// Ensure the environments directory exists
const targetDir = path.join(__dirname, '../src/environments');
if (!fs.existsSync(targetDir)) {
  fs.mkdirSync(targetDir, { recursive: true });
}

// Function to generate the environment file content
const generateEnvironmentContent = (isProduction) => {
  return `export const environment = {
  production: ${isProduction},
  apiBaseUrl: '/api',
  supabaseUrl: '${process.env.SUPABASE_URL || ''}',
  supabaseKey: '${process.env.SUPABASE_KEY || ''}'
};
`;
};

// Write the files
fs.writeFileSync(path.join(targetDir, 'environment.ts'), generateEnvironmentContent(false));
fs.writeFileSync(path.join(targetDir, 'environment.prod.ts'), generateEnvironmentContent(true));

console.log('Environment files generated successfully!');
