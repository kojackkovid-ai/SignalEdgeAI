// Quick fix script to patch the Dashboard.tsx file
const fs = require('fs');

const filePath = 'frontend/src/pages/Dashboard.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Fix 1: Handle undefined prediction in the map callback
content = content.replace(
  /setGameProps\(\(prev: any\[\]\) => prev\.map\(\(p: any\) => \s*p\.id === propId \? \{ \.\.\.p, unlocked: true, prediction: response\.data\.prediction \|\| p\.prediction \} : p\s*\)\);/,
  `setGameProps((prev: any[]) => prev.map((p: any) => {
          if (p.id === propId) {
            const predictionValue = response.data?.prediction || p?.prediction;
            return { ...p, unlocked: true, prediction: predictionValue };
          }
          return p;
        }));`
);

// Fix 2: Handle undefined prop.prediction in display
content = content.replace(
  /<span className="font-bold text-green-800 text-lg">\{prop\.prediction\}<\/span>/,
  '<span className="font-bold text-green-800 text-lg">{prop.prediction || \'N/A\'}</span>'
);

fs.writeFileSync(filePath, content);
console.log('Dashboard.tsx patched successfully');
