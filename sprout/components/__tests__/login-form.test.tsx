import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoginForm } from "../login-form";
import { vi } from "vitest";
import userEvent from "@testing-library/user-event";
import * as actions from "@/app/login/actions";

vi.mock("@/app/login/actions", () => ({
  login: vi.fn(),
}));

describe("LoginForm", () => {
  it("renders login form", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /login/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /forgot your password?/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /sign up/i })).toBeInTheDocument();
  });

  it("has required fields", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toBeRequired();
    expect(screen.getByLabelText(/password/i)).toBeRequired();
  });

  it("email and password inputs have correct types", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText(/email/i)).toHaveAttribute("type", "email");
    expect(screen.getByLabelText(/password/i)).toHaveAttribute(
      "type",
      "password"
    );
  });

  it("allows user to type in fields", async () => {
    render(<LoginForm />);
    const user = userEvent.setup();

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "hello@example.com");
    await user.type(passwordInput, "password123");

    expect(emailInput).toHaveValue("hello@example.com");
    expect(passwordInput).toHaveValue("password123");
  });

  it("calls login action when form is submitted", async () => {
    render(<LoginForm />);
    const user = userEvent.setup();
    const mockLogin = vi.mocked(actions.login);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "hello@example.com");
    await user.type(passwordInput, "password123");

    const button = screen.getByRole("button", { name: /Login/i });

    await user.click(button);
    expect(mockLogin).toBeCalled();
  });

  it("passes email and password to login action", async () => {
    render(<LoginForm />);
    const user = userEvent.setup();
    const mockLogin = vi.mocked(actions.login);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, "hello@example.com");
    await user.type(passwordInput, "password123");

    const button = screen.getByRole("button", { name: /Login/i });

    await user.click(button);

    expect(mockLogin).toBeCalled();
    
    const formData = mockLogin.mock.calls[0][0] as FormData

    expect(formData.get("email")).toBe("hello@example.com")
    expect(formData.get("password")).toBe("password123")
  });
});
