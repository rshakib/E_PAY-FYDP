import { motion } from 'motion/react';
import { Hash, Lock, Send, Check } from 'lucide-react';

interface ProcessingStepProps {
  currentStep: number;
  timestamp?: string;
}

export function ProcessingStep({ currentStep, timestamp }: ProcessingStepProps) {
  const steps = [
    {
      icon: Hash,
      title: 'Preparing transfer request...',
      description: 'Session and transfer details ready',
    },
    {
      icon: Lock,
      title: 'Verifying secure session...',
      description: 'Key material stays server-side',
    },
    {
      icon: Send,
      title: 'Submitting transfer...',
      description: 'Balance update in progress',
    },
  ];

  return (
    <div className="space-y-6">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isActive = currentStep === index;
        const isComplete = currentStep > index;

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.3 }}
            className={`flex items-start gap-4 ${
              isActive ? 'opacity-100' : isComplete ? 'opacity-60' : 'opacity-30'
            }`}
          >
            <div
              className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
                isComplete
                  ? 'bg-emerald-100 text-emerald-600'
                  : isActive
                  ? 'bg-blue-600 text-white'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {isComplete ? <Check size={24} /> : <Icon size={24} />}
            </div>
            <div className="flex-1">
              <h4 className="mb-1">{step.title}</h4>
              <p className="text-sm text-muted-foreground">{step.description}</p>
              {isActive && index === 1 && timestamp && (
                <p className="text-xs text-blue-600 mt-2 font-mono">
                  T: {timestamp}
                </p>
              )}
            </div>
            {isActive && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                className="w-6 h-6 border-3 border-blue-600 border-t-transparent rounded-full"
              />
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
