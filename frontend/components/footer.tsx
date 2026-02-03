export function Footer() {
  return (
    <footer className="border-t bg-muted/50">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} IACUC Protocol Generator. All rights reserved.
          </p>
          <p className="text-sm text-muted-foreground">
            AI-powered assistance for IACUC protocol preparation
          </p>
        </div>
      </div>
    </footer>
  );
}
