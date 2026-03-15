import React from 'react';
import { Link } from 'react-router-dom';
import { Ship, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const TermsOfServicePage = () => {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-9 h-9 bg-primary rounded-sm flex items-center justify-center">
                <Ship className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight">LFD Clock</span>
            </Link>
            <Link to="/">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold mb-8">Terms of Service</h1>
        
        <div className="prose prose-slate max-w-none">
          <p className="text-muted-foreground mb-6">Last updated: March 2026</p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p className="text-slate-600">
              By accessing or using LFD Clock ("Service"), you agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the Service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">2. Description of Service</h2>
            <p className="text-slate-600">
              LFD Clock provides container Last Free Day (LFD) tracking and SMS notification services for freight forwarders and logistics professionals. The Service includes:
            </p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2 mt-4">
              <li>Automated parsing of shipping documents via email or direct upload</li>
              <li>Dashboard for tracking container LFD deadlines</li>
              <li>SMS notifications at configurable intervals before LFD expiration</li>
              <li>Tools for sharing shipment information with trucking partners</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">3. User Responsibilities</h2>
            <p className="text-slate-600 mb-4">You agree to:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>Provide accurate and complete registration information</li>
              <li>Maintain the security of your account credentials</li>
              <li>Use the Service only for lawful purposes</li>
              <li>Not share your account with unauthorized users</li>
              <li>Ensure you have the right to upload and process the documents you submit</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">4. Service Limitations</h2>
            <p className="text-slate-600 mb-4">You acknowledge that:</p>
            <ul className="list-disc pl-6 text-slate-600 space-y-2">
              <li>AI-powered document parsing may not be 100% accurate. Always verify extracted data.</li>
              <li>SMS delivery depends on third-party carriers and is not guaranteed.</li>
              <li>The Service is provided for informational purposes and does not replace professional logistics management.</li>
              <li>We are not responsible for demurrage charges, missed deadlines, or other losses resulting from reliance on the Service.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">5. Payment Terms</h2>
            <p className="text-slate-600">
              Subscription fees are billed monthly in advance. All fees are non-refundable except as required by law. We reserve the right to modify pricing with 30 days notice. SMS notifications beyond your plan limits may incur additional charges.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">6. Intellectual Property</h2>
            <p className="text-slate-600">
              The Service, including its design, features, and content, is owned by LFD Clock. You retain ownership of the data you upload. By using the Service, you grant us a license to process your data solely to provide the Service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">7. Limitation of Liability</h2>
            <p className="text-slate-600">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, LFD CLOCK SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, DATA, OR BUSINESS OPPORTUNITIES, ARISING FROM YOUR USE OF THE SERVICE.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">8. Disclaimer of Warranties</h2>
            <p className="text-slate-600">
              THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED. WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR COMPLETELY SECURE.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">9. Termination</h2>
            <p className="text-slate-600">
              We may terminate or suspend your account at any time for violation of these Terms. You may cancel your account at any time. Upon termination, your right to use the Service ceases immediately.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">10. Governing Law</h2>
            <p className="text-slate-600">
              These Terms shall be governed by the laws of the Province of Alberta, Canada, without regard to conflict of law principles.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">11. Changes to Terms</h2>
            <p className="text-slate-600">
              We may update these Terms from time to time. We will notify you of material changes via email or through the Service. Continued use after changes constitutes acceptance of the new Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold mb-4">12. Contact</h2>
            <p className="text-slate-600">
              For questions about these Terms, contact us at:
              <br /><br />
              <strong>Email:</strong> legal@lfdclock.com
              <br />
              <strong>Address:</strong> Calgary, Alberta, Canada
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-8 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2026 LFD Clock. All rights reserved.
        </div>
      </footer>
    </div>
  );
};
