# ML Models Directory

Place your trained AlexNet model file here as `alexnet_leukemia.pt`.

If no model is found, the backend will run in **demo mode** using a randomly
initialised AlexNet, which is useful for testing the full UI/UX pipeline.

## Expected format
- PyTorch `state_dict` saved via `torch.save(model.state_dict(), path)`
- 4-class output: `["Benign", "Early Pre-B ALL", "Pre-B ALL", "Pro-B ALL"]`
