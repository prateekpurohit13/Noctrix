import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen bg-slate-900 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800" />
      <div className="absolute top-1/4 -left-48 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 -right-48 w-96 h-96 bg-teal-400/10 rounded-full blur-3xl" />
      
      <main className="relative z-10 flex flex-col items-center justify-center px-6 py-12 text-center max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="flex items-center justify-center w-12 h-12 bg-teal-500/10 rounded-xl border border-teal-500/20">
            <div className="w-6 h-6 bg-teal-500 rounded-lg" />
          </div>
          <span className="text-2xl font-bold text-white tracking-tight">Noctrix AI</span>
        </div>

        <h1 className="text-5xl font-bold tracking-tight text-white sm:text-6xl md:text-7xl leading-tight">
          Secure Document
          <span className="block mt-2 bg-gradient-to-r from-teal-400 to-teal-500 bg-clip-text text-transparent">
            Analysis Platform
          </span>
        </h1>
        
        <p className="mt-8 max-w-2xl text-lg text-slate-400 leading-relaxed">
          Leverage the power of AI to automatically cleanse, analyze, and assess
          your sensitive documents for security risks, all within a secure,
          privacy-preserving environment.
        </p>

        <div className="mt-12 flex flex-col sm:flex-row gap-4">
          <Link href="/login" passHref>
            <Button 
              size="lg" 
              className="px-8 py-6 text-base font-medium bg-teal-500 hover:bg-teal-600 text-white border-0 shadow-lg shadow-teal-500/25 transition-all duration-200"
            >
              Get Started
            </Button>
          </Link>
          <Button 
            size="lg" 
            variant="outline"
            className="px-8 py-6 text-base font-medium bg-transparent border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600 transition-all duration-200"
          >
            Learn More
          </Button>
        </div>

        <div className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-8 w-full max-w-3xl">
          <div className="flex flex-col items-center p-6 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-sm">
            <div className="w-12 h-12 mb-4 flex items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">Secure & Private</h3>
            <p className="text-xs text-slate-400 text-center">End-to-end encryption for your documents</p>
          </div>

          <div className="flex flex-col items-center p-6 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-sm">
            <div className="w-12 h-12 mb-4 flex items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">AI-Powered</h3>
            <p className="text-xs text-slate-400 text-center">Advanced machine learning analysis</p>
          </div>

          <div className="flex flex-col items-center p-6 rounded-2xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-sm">
            <div className="w-12 h-12 mb-4 flex items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">Real-time Results</h3>
            <p className="text-xs text-slate-400 text-center">Instant security risk assessment</p>
          </div>
        </div>
      </main>

      <footer className="relative z-10 w-full py-6 mt-auto border-t border-slate-800">
        <div className="flex flex-col sm:flex-row items-center justify-between px-8 text-xs text-slate-500 max-w-7xl mx-auto">
          <p>© {new Date().getFullYear()} Noctrix AI. All Rights Reserved.</p>
          <div className="flex gap-6 mt-2 sm:mt-0">
            <Link href="/privacy" className="hover:text-teal-400 transition-colors">Privacy</Link>
            <Link href="/terms" className="hover:text-teal-400 transition-colors">Terms</Link>
            <Link href="/contact" className="hover:text-teal-400 transition-colors">Contact</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}