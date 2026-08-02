import { Link } from 'react-router-dom';
import { MessageSquare, FileText, Target, Mic } from 'lucide-react';

export default function Home() {
  const features = [
    {
      title: "AI Career Advisor",
      description: "Ask any career question and get personalized advice, learning roadmaps, and course recommendations.",
      icon: <MessageSquare size={24} />,
      link: "/chat",
    },
    {
      title: "Resume Review",
      description: "Upload your resume and get professional, actionable feedback powered by AI to land your dream job.",
      icon: <FileText size={24} />,
      link: "/resume",
    },
    {
      title: "Skill Gap Analysis",
      description: "Compare your current skills against your target role and get a prioritized learning plan.",
      icon: <Target size={24} />,
      link: "/skill-gap",
    },
    {
      title: "Mock Interviews",
      description: "Practice behavioral and technical questions in a simulated interactive interview.",
      icon: <Mic size={24} />,
      link: "/interview",
    }
  ];

  return (
    <div>
      <header className="hero-section">
        <h1>Navigate Your Tech Career with Confidence</h1>
        <p className="hero-subtitle">
          Trailmark is your personal AI-powered career companion. From resume reviews to mock interviews, we provide the tools you need to succeed.
        </p>
      </header>

      <div className="features-grid">
        {features.map((feature, i) => (
          <div key={i} className="surface-panel feature-card">
            <div className="icon-wrapper">
              {feature.icon}
            </div>
            <h2>{feature.title}</h2>
            <p className="text-secondary mb-6">{feature.description}</p>
            <Link to={feature.link} className="btn-secondary">
              Get Started →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
