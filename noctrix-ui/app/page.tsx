import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <main className="flex flex-col items-center justify-center p-8 text-center">        
        <h1 className="mt-6 text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
          Secure Document Analysis Platform
        </h1>
        
        <p className="mt-6 max-w-2xl text-lg text-gray-600 dark:text-gray-400">
          Leverage the power of AI to automatically cleanse, analyze, and assess
          your sensitive documents for security risks, all within a secure,
          privacy-preserving environment.
        </p>

        <div className="mt-10">
          <Link href="/login" passHref>
            <Button size="lg" className="px-8 py-6 text-lg">
              Login to Get Started
            </Button>
          </Link>
        </div>
      </main>

      <footer className="absolute bottom-0 p-4 text-xs text-gray-500">
        © {new Date().getFullYear()} Noctrix AI. All Rights Reserved.
      </footer>
    </div>
  );
}