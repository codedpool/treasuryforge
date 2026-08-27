import Hero from "@/components/landing/Hero";
import Thesis from "@/components/landing/Thesis";
import DecisionLoop from "@/components/landing/DecisionLoop";
import Triggers from "@/components/landing/Triggers";
import SelfAudit from "@/components/landing/SelfAudit";
import ClosingCta from "@/components/landing/ClosingCta";

export default function LandingPage() {
  return (
    <main>
      <Hero />
      <Thesis />
      <DecisionLoop />
      <Triggers />
      <SelfAudit />
      <ClosingCta />
    </main>
  );
}
