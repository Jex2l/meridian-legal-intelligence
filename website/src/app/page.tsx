import Nav from "@/components/Nav";
import Hero from "@/components/Hero";
import Services from "@/components/Services";
import HowItWorks from "@/components/HowItWorks";
import Trust from "@/components/Trust";
import FAQ from "@/components/FAQ";
import About from "@/components/About";
import ContactCTA from "@/components/ContactCTA";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Services />
        <HowItWorks />
        <Trust />
        <FAQ />
        <About />
        <ContactCTA />
      </main>
      <Footer />
    </>
  );
}
