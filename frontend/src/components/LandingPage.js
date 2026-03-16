import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { 
  Mail, 
  Zap, 
  Bell, 
  ArrowRight, 
  Check, 
  Phone,
  ChevronRight,
  Anchor
} from 'lucide-react';

export const LandingPage = () => {
  // Carrier data with logo URLs
  const carriers = [
    { name: 'MAERSK', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Maersk_Group_Logo.svg/200px-Maersk_Group_Logo.svg.png' },
    { name: 'MSC', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/MSC_Logo.svg/200px-MSC_Logo.svg.png' },
    { name: 'CMA CGM', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/CMA_CGM_Company_Logo.svg/200px-CMA_CGM_Company_Logo.svg.png' },
    { name: 'COSCO', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/COSCO_logo.svg/200px-COSCO_logo.svg.png' },
    { name: 'HAPAG-LLOYD', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Hapag-Lloyd_logo.svg/200px-Hapag-Lloyd_logo.svg.png' },
    { name: 'ONE', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/ONE_LINE_logo.svg/200px-ONE_LINE_logo.svg.png' },
    { name: 'EVERGREEN', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Evergreen_Marine_Corporation_Logo.svg/200px-Evergreen_Marine_Corporation_Logo.svg.png' },
    { name: 'YANG MING', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Yang_Ming_Marine_Transport_logo.svg/200px-Yang_Ming_Marine_Transport_logo.svg.png' },
    { name: 'HMM', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Hyundai_Merchant_Marine_logo.svg/200px-Hyundai_Merchant_Marine_logo.svg.png' },
    { name: 'ZIM', logo: 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Zim_Integrated_Shipping_Services_Logo.svg/200px-Zim_Integrated_Shipping_Services_Logo.svg.png' },
  ];

  const steps = [
    {
      number: '01',
      title: 'Forward Your Emails',
      description: 'Send your shipping notifications to your unique @inbound.lfdclock.com address. Works with any carrier or freight forwarder.'
    },
    {
      number: '02',
      title: 'AI Extracts the Data',
      description: 'Our AI instantly parses container numbers, Last Free Days, and carrier details from PDFs and email content.'
    },
    {
      number: '03',
      title: 'Get SMS Alerts',
      description: 'Receive automatic SMS notifications at 48h, 24h, 12h, and 6h before each deadline. Never miss a pickup.'
    }
  ];

  const starterFeatures = [
    'Up to 25 containers/month',
    'SMS alerts (48h, 24h, 12h, 6h)',
    'AI email parsing',
    'Traffic light dashboard',
    'Single user'
  ];

  const enterpriseFeatures = [
    'Unlimited containers',
    'Custom alert schedules',
    'Priority AI parsing',
    'Multi-user access',
    'API access',
    'Dedicated support',
    'Custom integrations'
  ];

  return (
    <div className="landing-paper min-h-screen bg-[#FAF7F2] text-[#1A1A1A] overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 bg-grid-pattern pointer-events-none" />
      <div className="radial-glow -top-64 -right-64" />
      <div className="radial-glow top-1/2 -left-64" />
      
      {/* Navigation */}
      <nav className="relative z-50 border-b border-[#E8E2D9] bg-[#FAF7F2]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#FF4F00] rounded-lg flex items-center justify-center">
                <Anchor className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-[#1A1A1A]" style={{ fontFamily: 'Inter, sans-serif' }}>
                LFD Clock
              </span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button 
                  variant="ghost" 
                  className="btn-ghost-paper h-10 px-5"
                  data-testid="nav-login-btn"
                >
                  Sign In
                </Button>
              </Link>
              <Link to="/signup">
                <Button 
                  className="btn-accent-glow h-10 px-6 rounded-lg"
                  data-testid="nav-signup-btn"
                >
                  Join the Beta
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 lg:pt-32 lg:pb-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl">
            {/* Beta Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#FF4F00]/10 border border-[#FF4F00]/30 rounded-full text-sm font-medium text-[#FF4F00] mb-8">
              <span className="w-2 h-2 bg-[#FF4F00] rounded-full animate-pulse" />
              Now in Beta — Limited Spots Available
            </div>
            
            {/* Main Headline */}
            <h1 
              className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight mb-6"
              style={{ fontFamily: 'Inter, sans-serif', lineHeight: 1.1 }}
            >
              <span className="text-gradient-hero">Stop Paying</span>
              <br />
              <span className="text-[#1A1A1A]">Demurrage Fees.</span>
            </h1>
            
            {/* Subheadline */}
            <p className="text-lg sm:text-xl text-[#666666] mb-10 max-w-2xl leading-relaxed">
              LFD Clock automatically tracks your container Last Free Days and sends 
              SMS alerts before deadlines hit. Forward your shipping emails and let 
              our AI handle the rest.
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mb-16">
              <Link to="/signup">
                <Button 
                  size="lg" 
                  className="btn-accent-glow h-14 px-8 text-base rounded-xl"
                  data-testid="hero-cta-btn"
                >
                  Join the Beta
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/login">
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="btn-ghost-paper h-14 px-8 text-base rounded-xl"
                >
                  Sign In
                  <ChevronRight className="w-5 h-5 ml-1" />
                </Button>
              </Link>
            </div>

            {/* Stats Row */}
            <div className="flex flex-wrap gap-8 sm:gap-12">
              <div>
                <div className="text-3xl sm:text-4xl font-bold text-[#1A1A1A]">$300+</div>
                <div className="text-sm text-[#888888]">Avg. saved per container</div>
              </div>
              <div>
                <div className="text-3xl sm:text-4xl font-bold text-[#1A1A1A]">4</div>
                <div className="text-sm text-[#888888]">SMS alerts before LFD</div>
              </div>
              <div>
                <div className="text-3xl sm:text-4xl font-bold text-[#1A1A1A]">&lt;30s</div>
                <div className="text-sm text-[#888888]">AI parsing time</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof - Carrier Infinite Marquee */}
      <section className="relative py-12 border-y border-[#E8E2D9] bg-white/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs uppercase tracking-widest text-[#888888] mb-8">
            Works with all major carriers
          </p>
        </div>
        <div className="overflow-hidden">
          <div className="flex animate-marquee">
            {/* First set of logos */}
            {carriers.map((carrier, index) => (
              <div 
                key={`first-${index}`} 
                className="flex-shrink-0 mx-8 flex items-center justify-center h-12 w-32 grayscale hover:grayscale-0 opacity-60 hover:opacity-100 transition-all duration-300"
              >
                <img 
                  src={carrier.logo} 
                  alt={carrier.name}
                  className="max-h-10 max-w-full object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = `<span class="text-[#666666] font-semibold text-sm tracking-wider">${carrier.name}</span>`;
                  }}
                />
              </div>
            ))}
            {/* Duplicate set for seamless loop */}
            {carriers.map((carrier, index) => (
              <div 
                key={`second-${index}`} 
                className="flex-shrink-0 mx-8 flex items-center justify-center h-12 w-32 grayscale hover:grayscale-0 opacity-60 hover:opacity-100 transition-all duration-300"
              >
                <img 
                  src={carrier.logo} 
                  alt={carrier.name}
                  className="max-h-10 max-w-full object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = `<span class="text-[#666666] font-semibold text-sm tracking-wider">${carrier.name}</span>`;
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works - Vertical Steps */}
      <section className="relative py-24 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 
              className="text-3xl sm:text-4xl font-bold tracking-tight text-[#1A1A1A] mb-4"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              How It Works
            </h2>
            <p className="text-[#666666] text-lg max-w-xl mx-auto">
              Three simple steps to never miss a Last Free Day again
            </p>
          </div>
          
          <div className="max-w-3xl mx-auto space-y-8">
            {steps.map((step, index) => (
              <div 
                key={index}
                className="glass-card rounded-2xl p-8 relative"
              >
                <div className="flex items-start gap-6">
                  <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-[#FF4F00]/10 border border-[#FF4F00]/30 flex items-center justify-center">
                    <span className="text-[#FF4F00] font-bold text-lg" style={{ fontFamily: 'Inter, sans-serif' }}>
                      {step.number}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-[#1A1A1A] mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                      {step.title}
                    </h3>
                    <p className="text-[#666666] leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 border-y border-[#E8E2D9] bg-white/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="glass-card rounded-2xl p-8">
              <div className="feature-icon w-14 h-14 bg-[#F5F1E8] rounded-xl flex items-center justify-center mb-6">
                <Mail className="w-6 h-6 text-[#FF4F00]" />
              </div>
              <h3 className="text-xl font-semibold text-[#1A1A1A] mb-3" style={{ fontFamily: 'Inter, sans-serif' }}>
                Smart Email Parsing
              </h3>
              <p className="text-[#666666] leading-relaxed">
                Forward your freight notifications and our AI automatically extracts container data from PDFs and emails.
              </p>
            </div>
            
            <div className="glass-card rounded-2xl p-8">
              <div className="feature-icon w-14 h-14 bg-[#F5F1E8] rounded-xl flex items-center justify-center mb-6">
                <Zap className="w-6 h-6 text-[#FF4F00]" />
              </div>
              <h3 className="text-xl font-semibold text-[#1A1A1A] mb-3" style={{ fontFamily: 'Inter, sans-serif' }}>
                Real-Time Tracking
              </h3>
              <p className="text-[#666666] leading-relaxed">
                Visual traffic light system shows exactly how much time you have before each LFD expires.
              </p>
            </div>
            
            <div className="glass-card rounded-2xl p-8">
              <div className="feature-icon w-14 h-14 bg-[#F5F1E8] rounded-xl flex items-center justify-center mb-6">
                <Bell className="w-6 h-6 text-[#FF4F00]" />
              </div>
              <h3 className="text-xl font-semibold text-[#1A1A1A] mb-3" style={{ fontFamily: 'Inter, sans-serif' }}>
                Automated SMS Alerts
              </h3>
              <p className="text-[#666666] leading-relaxed">
                Get SMS notifications at 48h, 24h, 12h, and 6h intervals. Never miss a deadline again.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="relative py-24 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 
              className="text-3xl sm:text-4xl font-bold tracking-tight text-[#1A1A1A] mb-4"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Simple Pricing
            </h2>
            <p className="text-[#666666] text-lg max-w-xl mx-auto">
              Start free during beta. Scale as your volume grows.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Starter Plan */}
            <div className="pricing-card rounded-2xl p-8">
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-[#666666] mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                  Starter
                </h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-[#1A1A1A]">$49</span>
                  <span className="text-[#888888]">/month</span>
                </div>
                <p className="text-sm text-[#FF4F00] mt-2">Free during beta</p>
              </div>
              
              <ul className="space-y-4 mb-8">
                {starterFeatures.map((feature, index) => (
                  <li key={index} className="flex items-center gap-3 text-[#444444]">
                    <Check className="w-5 h-5 text-[#FF4F00] flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <Link to="/signup">
                <Button 
                  className="w-full btn-ghost-paper h-12 rounded-xl"
                  data-testid="pricing-starter-btn"
                >
                  Start Free Trial
                </Button>
              </Link>
            </div>
            
            {/* Enterprise Plan */}
            <div className="pricing-card featured rounded-2xl p-8">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="px-4 py-1 bg-[#FF4F00] text-white text-xs font-semibold rounded-full uppercase tracking-wider">
                  Popular
                </span>
              </div>
              
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-[#666666] mb-2" style={{ fontFamily: 'Inter, sans-serif' }}>
                  Enterprise
                </h3>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-[#1A1A1A]">$199</span>
                  <span className="text-[#888888]">/month</span>
                </div>
                <p className="text-sm text-[#FF4F00] mt-2">Contact for beta pricing</p>
              </div>
              
              <ul className="space-y-4 mb-8">
                {enterpriseFeatures.map((feature, index) => (
                  <li key={index} className="flex items-center gap-3 text-[#444444]">
                    <Check className="w-5 h-5 text-[#FF4F00] flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <Link to="/signup">
                <Button 
                  className="w-full btn-accent-glow h-12 rounded-xl"
                  data-testid="pricing-enterprise-btn"
                >
                  Contact Sales
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="relative py-24 border-t border-[#E8E2D9] bg-gradient-to-b from-white/50 to-[#FAF7F2]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 
            className="text-3xl sm:text-4xl font-bold tracking-tight text-[#1A1A1A] mb-6"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Ready to Stop Paying Demurrage?
          </h2>
          <p className="text-[#666666] text-lg mb-10 max-w-xl mx-auto">
            Join freight forwarders who are saving thousands with automated LFD tracking.
          </p>
          <Link to="/signup">
            <Button 
              size="lg"
              className="btn-accent-glow h-14 px-10 text-base rounded-xl"
              data-testid="footer-cta-btn"
            >
              Join the Beta — It's Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-[#E8E2D9] py-12 bg-white/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row justify-between items-center gap-8">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-[#F5F1E8] rounded-lg flex items-center justify-center">
                <Anchor className="w-4 h-4 text-[#FF4F00]" />
              </div>
              <span className="font-semibold text-[#1A1A1A]" style={{ fontFamily: 'Inter, sans-serif' }}>
                LFD Clock
              </span>
            </div>
            
            {/* Contact Info */}
            <div className="flex flex-col sm:flex-row items-center gap-6 text-sm text-[#666666]">
              <a 
                href="mailto:info@lfdclock.com" 
                className="footer-link flex items-center gap-2 hover:text-[#1A1A1A] transition-colors"
              >
                <Mail className="w-4 h-4" />
                info@lfdclock.com
              </a>
              <a 
                href="tel:+18257607425" 
                className="footer-link flex items-center gap-2 hover:text-[#1A1A1A] transition-colors"
              >
                <Phone className="w-4 h-4" />
                +1 825 760 7425
              </a>
            </div>
            
            {/* Links */}
            <div className="flex items-center gap-6 text-sm">
              <Link to="/privacy" className="footer-link text-[#666666]">
                Privacy
              </Link>
              <Link to="/terms" className="footer-link text-[#666666]">
                Terms
              </Link>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-[#E8E2D9] text-center">
            <p className="text-xs text-[#888888]">
              © 2026 LFD Clock. Built for freight forwarders who value their time.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
