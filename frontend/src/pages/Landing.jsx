import { Link, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { STATUS } from '../theme/palette'

const AGENTS = [
  {
    key: 'finance',
    label: 'Finance Agent',
    description: 'Manages budgets, revenue tracking, expense management, and financial forecasting',
    icon: '💰',
    color: '#10B981'
  },
  {
    key: 'marketing',
    label: 'Marketing Agent',
    description: 'Handles campaigns, market analysis, customer engagement, and brand strategy',
    icon: '📈',
    color: '#3B82F6'
  },
  {
    key: 'hr',
    label: 'HR Agent',
    description: 'Manages recruitment, payroll, team performance, and employee satisfaction',
    icon: '👥',
    color: '#8B5CF6'
  },
  {
    key: 'operations',
    label: 'Operations Agent',
    description: 'Oversees supply chain, resource allocation, process optimization, and logistics',
    icon: '⚙️',
    color: '#F59E0B'
  },
  {
    key: 'ceo',
    label: 'CEO Agent',
    description: 'Strategic decision-making, cross-department coordination, and long-term vision',
    icon: '🎯',
    color: '#EF4444'
  }
]

const FEATURES = [
  {
    title: 'Multi-Agent Simulation',
    description: 'Five autonomous AI agents collaborate and compete to run a virtual startup, each with specialized expertise.',
    icon: '🤖'
  },
  {
    title: 'Real-time Decision Making',
    description: 'Watch agents make decisions in real-time based on business context, market conditions, and internal metrics.',
    icon: '⚡'
  },
  {
    title: 'Memory & Learning',
    description: 'Agents maintain persistent memory across simulation runs, learning from past decisions and outcomes.',
    icon: '🧠'
  },
  {
    title: 'Business Context Injection',
    description: 'Define your brand voice, product details, marketing strategy, and financial parameters to guide agent behavior.',
    icon: '📋'
  },
  {
    title: 'Interactive Dashboard',
    description: 'Monitor agent performance, view decision feeds, track metrics, and intervene with custom policies.',
    icon: '📊'
  },
  {
    title: 'Simulation Controls',
    description: 'Run, pause, step through, or fast-forward simulation ticks. Configure scenarios and inject events.',
    icon: '🎮'
  }
]

function Landing() {
  const token = useSelector((state) => state.auth.token)
  if (token) return <Navigate to="/app" replace />

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
        <section className="relative overflow-hidden py-20 sm:py-32">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight">
                AI-Powered Business{' '}
                <span className="relative">
                  <span className="relative z-10">Simulation</span>
                  <span
                    className="absolute bottom-2 left-0 right-0 h-4"
                    style={{ backgroundColor: `${STATUS.good}33` }}
                  />
                </span>
              </h2>
              <p className="mt-6 text-lg sm:text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
                Experience the future of business management with autonomous AI agents that collaborate,
                compete, and learn to run a virtual startup. Build, simulate, and optimize — all without writing code.
              </p>
              <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  to="/register"
                  className="w-full sm:w-auto px-8 py-3.5 text-base font-semibold text-white rounded-xl transition-all hover:shadow-lg"
                  style={{ backgroundColor: STATUS.good }}
                >
                  Start Your Free Simulation
                </Link>
                <Link
                  to="/login"
                  className="w-full sm:w-auto px-8 py-3.5 text-base font-semibold text-gray-700 rounded-xl border border-gray-300 transition-all hover:bg-gray-50"
                >
                  Sign In to Dashboard
                </Link>
              </div>
            </div>

            <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
              {AGENTS.map((agent) => (
                <div
                  key={agent.key}
                  className="group p-6 rounded-2xl border border-gray-100 bg-white hover:border-gray-200 hover:shadow-xl transition-all duration-300"
                >
                  <div
                    className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl mb-4 transition-transform group-hover:scale-110"
                    style={{ backgroundColor: `${agent.color}15` }}
                  >
                    {agent.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{agent.label}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{agent.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 sm:py-28 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">Why Startup Simulator?</h2>
              <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
                Built for entrepreneurs, students, and AI enthusiasts to understand how autonomous agents
                can transform business operations.
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {FEATURES.map((feature, index) => (
                <div
                  key={index}
                  className="p-6 rounded-2xl bg-white border border-gray-100 hover:shadow-lg transition-shadow"
                >
                  <div className="text-3xl mb-4">{feature.icon}</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 sm:py-28">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-gray-900 rounded-3xl p-8 sm:p-12 lg:p-16 text-center">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
                Ready to Build Your AI Startup?
              </h2>
              <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">
                Join thousands of users exploring the intersection of AI and business. Create your first
                simulation in minutes — no credit card required.
              </p>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 px-8 py-3.5 text-base font-semibold text-gray-900 rounded-xl transition-all hover:shadow-xl"
                style={{ backgroundColor: STATUS.good }}
              >
                Create Free Account
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
            </div>
          </div>
        </section>

        <section className="py-16 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Tech Stack</h3>
            <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-gray-500">
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">React 18</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">Redux Toolkit</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">Tailwind CSS</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">FastAPI</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">MongoDB</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">LangGraph</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">Groq LLM</span>
              <span className="px-3 py-1 rounded-full bg-white border border-gray-200">Docker</span>
            </div>
          </div>
        </section>

        <footer className="border-t border-gray-100 bg-white py-12 mt-16">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Startup Simulator</h4>
              <p className="text-sm text-gray-600">
                Multi-agent AI-powered business simulation platform for learning and experimentation.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Agents</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>Finance Agent</li>
                <li>Marketing Agent</li>
                <li>HR Agent</li>
                <li>Operations Agent</li>
                <li>CEO Agent</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Resources</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>Documentation</li>
                <li>API Reference</li>
                <li>Community Forum</li>
                <li>GitHub Repository</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Legal</h4>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>Privacy Policy</li>
                <li>Terms of Service</li>
                <li>Cookie Policy</li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-100 text-center text-sm text-gray-500">
            <p>© 2024 Startup Simulator. Built with ❤️ for the AI community.</p>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default Landing