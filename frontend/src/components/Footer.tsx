import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Phone } from 'lucide-react';

const Footer: React.FC = () => {
  const navigate = useNavigate();

  const legalPages = [
    { label: 'Terms of Service', path: '/legal/terms' },
    { label: 'Privacy Policy', path: '/legal/privacy' },
    { label: 'Responsible Gambling', path: '/legal/responsible-gambling' },
    { label: 'Refund Policy', path: '/legal/refund' },
    { label: 'Cookie Policy', path: '/legal/cookies' },
    { label: 'Risk Disclosure', path: '/legal/risk' },
  ];

  return (
    <footer className="bg-slate-950 text-slate-300 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Company Info */}
          <div>
            <h3 className="text-white font-bold mb-4">SignalEdge AI</h3>
            <p className="text-sm leading-relaxed">
              AI-powered sports prediction engine providing accurate predictions for major sports leagues.
            </p>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              {legalPages.map((link) => (
                <li key={link.path}>
                  <button
                    onClick={() => navigate(link.path)}
                    className="hover:text-cyan-400 transition-colors"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-white font-semibold mb-4">Support</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <a href="mailto:support@sportspredictionplatform.com" className="hover:text-cyan-400 transition-colors flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Email Support
                </a>
              </li>
              <li>
                <a href="mailto:billing@sportspredictionplatform.com" className="hover:text-cyan-400 transition-colors flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  Billing
                </a>
              </li>
              <li>
                <a href="tel:1-800-GAMBLER" className="hover:text-cyan-400 transition-colors flex items-center gap-2">
                  <Phone className="w-4 h-4" />
                  Problem Gambling
                </a>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="https://www.gamblersanonymous.org" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">
                  Gamblers Anonymous
                </a>
              </li>
              <li>
                <a href="https://www.ncpg.org" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">
                  NCPG Help
                </a>
              </li>
              <li>
                <a href="https://www.samhsa.gov" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">
                  SAMHSA Resources
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-slate-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-slate-500">
              © 2026 SignalEdge AI. All rights reserved.
            </p>
            <div className="flex gap-6 text-xs">
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">
                Twitter
              </a>
              <a href="https://discord.com" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">
                Discord
              </a>
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors">
                Instagram
              </a>
            </div>
          </div>

          {/* Warning Banner */}
          <div className="mt-8 p-4 bg-red-950 border border-red-800 rounded-lg">
            <p className="text-xs text-red-300">
              <strong>⚠️ Gambling Warning:</strong> Sports betting can be addictive. Please gamble responsibly. For help, contact the National Problem Gambling Helpline at 1-800-522-4700 or visit www.ncpg.org
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
