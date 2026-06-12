import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div className={cn("bg-card border border-border rounded-lg shadow-sm overflow-hidden", className)} {...props} />
  );
}

export function CardHeader({ className, ...props }: CardProps) {
  return (
    <div className={cn("px-6 py-4 border-b border-border flex flex-col space-y-1.5", className)} {...props} />
  );
}

export function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn("text-lg font-semibold leading-none tracking-tight", className)} {...props} />
  );
}

export function CardContent({ className, ...props }: CardProps) {
  return (
    <div className={cn("p-6", className)} {...props} />
  );
}
