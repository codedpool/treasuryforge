import Hero from "@/components/landing/Hero";
import HowItWorks from "@/components/landing/HowItWorks";
import RiskAndOversight from "@/components/landing/RiskAndOversight";
import ClosingCta from "@/components/landing/ClosingCta";

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <HowItWorks />
      <RiskAndOversight />
      <ClosingCta />
    </main>
  );
}
